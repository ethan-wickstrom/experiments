# OpenType engineering requirements for a monospaced family built with fontTools / ufo2ft / fontmake

Research date: 2026-11-14/15. Every claim carries its source at the claim. Three kinds of evidence are used and labelled:

- **[spec]/[source]** — a primary document or source file that I read (URL given).
- **[measured]** — I built a small programmatic monospaced test family ("Testmono": 102 glyphs, 3 upright + 3 italic UFO masters, one designspace) and inspected or checked the binaries. Tool versions: fontTools 4.68.0, ufo2ft 3.11.0, fontmake 3.12.2, fontbakery 1.1.0, ttfautohint-py 0.6.1 (bundled ttfautohint 1.8.4), afdko 5.0.1 (otfautohint), booleanOperations 0.10.0, skia-pathops 0.9.2, Python 3.13. Scripts and outputs are in `/tmp/claude-0/-home-user-experiments/a86123d7-7ed9-5f3d-9952-1d096afee651/scratchpad/research/ote/build/` (`gen.py`, `inspect_fonts.py`, `post.py`, `fbsum.py`, `fb/*.json`).
- **[inference]** — my own reasoning from the above; not stated by a source.

Source code of fontTools, ufo2ft, fontmake and fontbakery was read from the installed packages at the versions above; links point to the same files upstream.

---

## (a) Fields that mark a font as monospaced

### What each field must contain

| Field | Correct value for our font | Source |
|---|---|---|
| `post.isFixedPitch` (uint32) | non-zero (ufo2ft writes `1`) | "Set to 0 if the font is proportionally spaced, non-zero if the font is not proportionally spaced (i.e. monospaced)" — [post spec](https://learn.microsoft.com/en-us/typography/opentype/spec/post) |
| `'CFF '` Top DICT `isFixedPitch` (operator 12 1) | `1` (default is 0 = false) | [Adobe TN #5176, CFF spec, Top DICT table](https://adobe-type-tools.github.io/font-tech-notes/pdfs/5176.CFF.pdf) |
| `OS/2.panose` byte 4 `bProportion` | `9` when byte 1 `bFamilyType` = 2 (Latin Text) | The spec says "Proportion (for Family Kind = Latin Text) might be used to determine if a font is monospaced" and defers values to the PANOSE guide — [OS/2 spec](https://learn.microsoft.com/en-us/typography/opentype/spec/os2#panose). fontbakery encodes the rule as: Latin Text → `bProportion == 9`; Latin Hand Written / Latin Symbol → 4th digit `== 3` — [monospace.py](https://github.com/fonttools/fontbakery/blob/main/Lib/fontbakery/checks/opentype/monospace.py) |
| `OS/2.xAvgCharWidth` | the cell advance (e.g. 600) | OS/2 v3+: "the arithmetic average of the escapement (width) of all non-zero width glyphs in the font" — [OS/2 spec](https://learn.microsoft.com/en-us/typography/opentype/spec/os2#xavgcharwidth). fontTools computes exactly that (`width > 0` only, `otRound`) — [O_S_2f_2.py `recalcAvgCharWidth`](https://github.com/fonttools/fonttools/blob/main/Lib/fontTools/ttLib/tables/O_S_2f_2.py); ufo2ft calls it — [outlineCompiler.py `setupTable_OS2`](https://github.com/googlefonts/ufo2ft/blob/main/Lib/ufo2ft/outlineCompiler.py) |
| `hhea.advanceWidthMax` | the cell advance | "Maximum advance width value in 'hmtx' table" — [hhea spec](https://learn.microsoft.com/en-us/typography/opentype/spec/hhea) |
| `hhea.numberOfHMetrics` | whatever the compiler emits (see below) | "It is suggested that monospaced fonts set numberOfHMetrics to three" — [recommendations](https://learn.microsoft.com/en-us/typography/opentype/spec/recom#hhea-table) |

With zero-width combining marks present, the average of non-zero widths is exactly the cell advance, so `xAvgCharWidth` = advance. **[measured]**: 600 in every build (advances were {0, 600}).

### What ufo2ft does by default — nothing is automatic

**[source]** [ufo2ft fontInfoData.py](https://github.com/googlefonts/ufo2ft/blob/main/Lib/ufo2ft/fontInfoData.py) `staticFallbackData`: `postscriptIsFixedPitch=False`, `openTypeOS2Panose=[0]*10`. ufo2ft copies `postscriptIsFixedPitch` to both `post.isFixedPitch` and the CFF Top DICT ([outlineCompiler.py](https://github.com/googlefonts/ufo2ft/blob/main/Lib/ufo2ft/outlineCompiler.py), `setupTable_post`, `setupTable_CFF`). It never inspects the advances.

**[measured]** A UFO with only family/style name, UPM and vertical dimensions, all advances 600 or 0, compiles to `post.isFixedPitch=0`, CFF `isFixedPitch=0`, PANOSE all zero. With `postscriptIsFixedPitch = True` and `openTypeOS2Panose = [2, 11, 5, 9, 0, 0, 0, 0, 0, 0]` it compiles to `post.isFixedPitch=1`, CFF `isFixedPitch=1`, `bProportion=9`.

One side effect: for interpolated instances, fontmake's instantiator keeps only PANOSE digits shared by all sources ("only copy panose values that are shared by all the designspace.sources", [ufo2ft instantiator.py](https://github.com/googlefonts/ufo2ft/blob/main/Lib/ufo2ft/instantiator.py)). **[measured]**: Medium Italic came out as `[2, 11, 0, 9, …]` because the masters' weight digit differed. `bProportion` survives as long as every master sets 9.

### `numberOfHMetrics`: 3 is not reachable with zero-width marks, and that is acceptable

- **[source]** fontTools computes the count itself at compile time by trimming the trailing run of equal advances ([_h_m_t_x.py `compile`](https://github.com/fonttools/fonttools/blob/main/Lib/fontTools/ttLib/tables/_h_m_t_x.py)); ufo2ft precomputes the same number. There is no option to force 3.
- **[measured]** Effect of glyph order on a 102-glyph font with 2 zero-width marks: marks immediately after `.notdef` → `numberOfHMetrics = 4`, `hmtx` 212 bytes; marks near the end → 100, 404 bytes; marks last → 101, 406 bytes. General rule **[inference]**: with all zero-width glyphs placed directly after `.notdef`, `numberOfHMetrics = (number of zero-width glyphs) + 2`.
- fontbakery only **WARN**s (`bad-numberOfHMetrics`) when the value is not 3 and points to [fonttools issue #3014](https://github.com/fonttools/fonttools/issues/3014) "to decide whether this makes sense for your font". In that thread (read through a page summary, so medium confidence on exact wording) the maintainers call 3 an optimisation hint, note that "most monospace fonts these days are not truly 'monospaced' because of zerowidth marks", and the issue was closed as not planned.
- The same recommendations page says "OpenType fonts that include CFF data must set numberOfHMetrics equal to the number of glyphs" ([recom, hmtx](https://learn.microsoft.com/en-us/typography/opentype/spec/recom#hmtx-table)). **[measured]** fontTools does not follow this: the CFF build had `numberOfHMetrics=100` for 102 glyphs. OTS (run by fontbakery's `ots` check) accepted the file.

### How fontbakery decides "is this monospaced" and what it then checks

**[source]** [conditions.py `glyph_metrics_stats`](https://github.com/fonttools/fontbakery/blob/main/Lib/fontbakery/checks/conditions.py) and [monospace.py](https://github.com/fonttools/fontbakery/blob/main/Lib/fontbakery/checks/opentype/monospace.py):

1. If the font maps more than 80 % of U+0020–U+007E (i.e. > 76 of 95), it "seems monospaced" when at least 80 % of the **non-zero** ASCII advances share one width. Otherwise: all cmapped letters/marks/numbers/punctuation/symbols/spaces, **minus GDEF mark-class glyphs**, with advance ≠ 0, must have at most 2 distinct widths.
2. Zero-width glyphs are ignored everywhere: `most_common_width` is computed over advances ≠ 0, and the outlier list excludes glyphs whose advance is 0 and the glyphs named `.notdef`, `.null`, `NULL`.
3. If it seems monospaced: FAIL `mono-bad-panose` unless PANOSE says monospaced; WARN `mono-outliers` listing every glyph whose advance is neither 0 nor the common width; FAIL `mono-bad-post-isFixedPitch` if `post.isFixedPitch == 0` (only evaluated when there are no outliers); WARN `bad-numberOfHMetrics` if ≠ 3. Always: FAIL `bad-advanceWidthMax` if `hhea.advanceWidthMax` ≠ the true maximum.
4. If it does not seem monospaced, the check FAILs when `isFixedPitch` is set or `bProportion == 9`.

`opentype/xavgcharwidth` ([source](https://github.com/fonttools/fontbakery/blob/main/Lib/fontbakery/checks/opentype/xavgcharwidth.py)) recomputes the average over advances > 0; a difference of 1 passes, < 10 is INFO, otherwise WARN.

Marks: `opentype/gdef_spacing_marks` is in the profile; glyphs in the GDEF mark class are expected to have zero advance ([opentype profile](https://github.com/fonttools/fontbakery/blob/main/Lib/fontbakery/profiles/opentype.py)). So zero-width, GDEF-classed combining marks are the convention the checks assume.

**[measured]** `opentype/monospace` raises ERROR (`failed-check`) on every CFF `.otf` in fontbakery 1.1.0, because the check reads `ttFont["glyf"]`. It ran on all 10 static OTFs with that result. Monospace metadata of OTFs therefore has to be asserted by our own test.

### Who reads which field (why all of them must be set)

- FreeType sets `FT_FACE_FLAG_FIXED_WIDTH` from `post.isFixedPitch` — [sfobjs.c](https://raw.githubusercontent.com/freetype/freetype/master/src/sfnt/sfobjs.c).
- fontconfig does **not** trust that flag (the code path is `#if 0`'d with the comment "most other fonts don't bother to set the attribute"); it measures the advances of all cmapped glyphs, **ignores advances ≤ 0**, and reports `spacing=mono` when all remaining advances fall in one cluster within a tolerance of 1/33 — [fcfreetype.c `FcFreeTypeSpacing` / `FcSpacingClassify`](https://gitlab.freedesktop.org/fontconfig/fontconfig/-/raw/main/src/fcfreetype.c). Consequence **[inference]**: a single cmapped glyph with a different non-zero advance (e.g. a double-width glyph) changes the classification path; zero-width marks do not.
- Gecko on Windows takes its `maxAdvance` from `hhea.advanceWidthMax` — [gfxDWriteFonts.cpp](https://raw.githubusercontent.com/mozilla-firefox/firefox/main/gfx/thebes/gfxDWriteFonts.cpp).
- Terminals measure the cell from ASCII advances, not from flags: kitty takes the maximum `ceil(advance)` over U+0020–U+007F ([freetype.c `calc_cell_width`](https://raw.githubusercontent.com/kovidgoyal/kitty/master/kitty/freetype.c)), WezTerm the maximum over 32–127 ([ftwrap.rs](https://raw.githubusercontent.com/wezterm/wezterm/main/wezterm-font/src/ftwrap.rs)), Ghostty the maximum over printable ASCII then `round` ([freetype.zig](https://raw.githubusercontent.com/ghostty-org/ghostty/main/src/font/face/freetype.zig), [Metrics.zig](https://raw.githubusercontent.com/ghostty-org/ghostty/main/src/font/Metrics.zig)), Alacritty `floor` of the advance of `0` ([crossfont ft/mod.rs](https://raw.githubusercontent.com/alacritty/crossfont/master/src/ft/mod.rs), [display/mod.rs](https://raw.githubusercontent.com/alacritty/alacritty/master/alacritty/src/display/mod.rs)), Windows Terminal `round` of the advance of `0` ([AtlasEngine.api.cpp](https://raw.githubusercontent.com/microsoft/terminal/main/src/renderer/atlas/AtlasEngine.api.cpp)).

---

## (b) Vertical metrics: one line height everywhere

### What the specification says

- Three sets exist because "legacy platform implementations used those fields with platform-specific behaviors": `hhea` (Apple), `OS/2.sTypo*` (portable), `OS/2.usWin*` (GDI clipping) — [OS/2 spec, sTypoAscender](https://learn.microsoft.com/en-us/typography/opentype/spec/os2#stypoascender), [hhea spec](https://learn.microsoft.com/en-us/typography/opentype/spec/hhea).
- `fsSelection` bit 7 `USE_TYPO_METRICS`: "it is strongly recommended that applications use OS/2.sTypoAscender - OS/2.sTypoDescender + OS/2.sTypoLineGap as the default line spacing"; "For new fonts, vendors are encouraged to use a version 4 or later OS/2 table and to have bit 7 set" — [OS/2 spec, fsSelection](https://learn.microsoft.com/en-us/typography/opentype/spec/os2#fsselection).
- GDI clips at `usWinAscent` / `usWinDescent`: "If any clipping is unacceptable, then the value should be set greater than or equal to yMax" — [OS/2 spec, usWinAscent](https://learn.microsoft.com/en-us/typography/opentype/spec/os2#uswinascent).
- "Negative lineGap values are treated as zero in some legacy platform implementations" — [hhea spec](https://learn.microsoft.com/en-us/typography/opentype/spec/hhea).
- The recommendations chapter gives two recipes ([recom, Baseline to Baseline Distances](https://learn.microsoft.com/en-us/typography/opentype/spec/recom#baseline-to-baseline-distances)). The "alternative guidance" is the one that makes every formula equal:
  - set `USE_TYPO_METRICS`;
  - `hhea.ascender = usWinAscent = sTypoAscender`;
  - `hhea.descender = -usWinDescent = sTypoDescender`;
  - `hhea.lineGap = sTypoLineGap = 0`.
- GDI's own numbers per the same page: `tmAscent = usWinAscent`, `tmDescent = usWinDescent`, `tmExternalLeading = MAX(0, (hhea.ascender - hhea.descender + hhea.lineGap) - (usWinAscent + usWinDescent))`.

### What Google Fonts requires

[GF guide, Vertical metrics](https://googlefonts.github.io/gf-guide/metrics.html):

1. Same values in every font of the family.
2. `Use_Typo_Metrics` enabled.
3. `winAscent` / `winDescent` = the family's tallest `yMax` / deepest `yMin`.
4. hhea and typo "should be equal".
5. "LineGap values must be 0" (both).
6. Capitals centred: `typoAscender − capHeight = abs(typoDescender)`.
7. `typoAscender` ≥ height of Ắ (U+1EAE); À (U+00C0) is the required minimum because "Certain Mac applications, including TextEdit, determine the height of the first line of text by either the Agrave U+00C0 height or the font's hheaAscender, whichever is taller".
8. ascender + |descender| + lineGap should be 120–130 % of UPM (example: 900 / −300 at 1000 UPM).
9. Once published "vertical metric values cannot be modified".

fontbakery's encoding of this: `os2_metrics_match_hhea` FAILs unless typo asc/desc/gap equal hhea ([source](https://github.com/fonttools/fontbakery/blob/main/Lib/fontbakery/checks/os2_metrics_match_hhea.py)); `linegaps` WARNs on non-zero gaps ([source](https://github.com/fonttools/fontbakery/blob/main/Lib/fontbakery/checks/linegaps.py)); `family/win_ascent_and_descent` FAILs unless `yMax ≤ usWinAscent ≤ 2·yMax` and `|yMin| ≤ usWinDescent ≤ 2·|yMin|`, measured across all files passed together ([source](https://github.com/fonttools/fontbakery/blob/main/Lib/fontbakery/checks/family/win_ascent_and_descent.py)); `googlefonts/vertical_metrics` FAILs on non-zero gaps or when (hhea asc + |desc| + gap)/UPM is < 1.2 or > 2.0, WARNs above 1.5 ([source](https://github.com/fonttools/fontbakery/blob/main/Lib/fontbakery/checks/vendorspecific/googlefonts/vertical_metrics.py)).

### What ufo2ft produces if we set nothing — three different line heights

**[source]** fallbacks in [fontInfoData.py](https://github.com/googlefonts/ufo2ft/blob/main/Lib/ufo2ft/fontInfoData.py): `openTypeOS2TypoLineGap = max(int(UPM*1.2) − ascender + descender, 0)`; `openTypeHheaAscender = ascender + typoLineGap`; `openTypeHheaLineGap = 0`; `openTypeOS2WinAscent = ascender + typoLineGap`; `openTypeOS2WinDescent = abs(descender)`; `openTypeOS2Selection = []` (bit 7 off).

**[measured]** UFO with ascender 800, descender −200, UPM 1000 → hhea 1000 / −200 / 0, typo 800 / −200 / 200, win 1000 / 200, `fsSelection = 0x0040`. fontbakery then reports FAIL `os2_metrics_match_hhea`, FAIL `family/win_ascent_and_descent` (a descender at −230 exceeded win 200), WARN `linegaps`.

### How each consumer derives line / cell height

| Consumer | Rule | Source |
|---|---|---|
| FreeType `face->ascender/descender/height` | bit 7 set → sTypo asc/desc and `asc − desc + sTypoLineGap`; else hhea; if hhea asc and desc are both 0 → sTypo if non-zero, else usWin | [sfobjs.c](https://raw.githubusercontent.com/freetype/freetype/master/src/sfnt/sfobjs.c) |
| kitty (Linux) | `cell_height = ceil(face.height × y_scale)`; baseline = `ceil(ascender)`; raised if `_` would fall outside | [freetype.c](https://raw.githubusercontent.com/kovidgoyal/kitty/master/kitty/freetype.c) |
| kitty (macOS) | distance between two CoreText line origins, `ceil` | [core_text.m](https://raw.githubusercontent.com/kovidgoyal/kitty/master/kitty/core_text.m) |
| Ghostty | reads hhea and OS/2 itself with the same priority as FreeType; `cell_height = round(ascent − descent + line_gap)`; half the gap above, half below | [freetype.zig](https://raw.githubusercontent.com/ghostty-org/ghostty/main/src/font/face/freetype.zig), [Metrics.zig](https://raw.githubusercontent.com/ghostty-org/ghostty/main/src/font/Metrics.zig) |
| Alacritty | FreeType: `max(size_metrics.height, ascender − descender)`; macOS: `round(ascent)+round(descent)+round(leading)`; Windows: `(ascent + descent + lineGap) × scale` from `DWRITE_FONT_METRICS`; then `floor` | [crossfont ft](https://raw.githubusercontent.com/alacritty/crossfont/master/src/ft/mod.rs), [darwin](https://raw.githubusercontent.com/alacritty/crossfont/master/src/darwin/mod.rs), [directwrite](https://raw.githubusercontent.com/alacritty/crossfont/master/src/directwrite/mod.rs), [display/mod.rs](https://raw.githubusercontent.com/alacritty/alacritty/master/alacritty/src/display/mod.rs) |
| WezTerm | `y_scale × face.height / 64` | [ftwrap.rs](https://raw.githubusercontent.com/wezterm/wezterm/main/wezterm-font/src/ftwrap.rs) |
| Windows Terminal | `round((ascent + descent + lineGap)/designUnitsPerEm × fontSizePx)` from `DWRITE_FONT_METRICS`; baseline = `round(ascent + (lineGap + cell − advanceHeight)/2)` | [AtlasEngine.api.cpp](https://raw.githubusercontent.com/microsoft/terminal/main/src/renderer/atlas/AtlasEngine.api.cpp) |
| VTE (GNOME Terminal etc.) | maximum Pango logical height over U+0021–U+007E, `ceil`; Pango font metrics used when at least as tall | [fonts-pangocairo.cc](https://gitlab.gnome.org/GNOME/vte/-/raw/master/src/fonts-pangocairo.cc) |
| xterm.js (VS Code terminal) | DOM `offsetHeight` of a measuring span, or canvas `fontBoundingBoxAscent + fontBoundingBoxDescent` | [CharSizeService.ts](https://raw.githubusercontent.com/xtermjs/xterm.js/master/src/browser/services/CharSizeService.ts) |
| VS Code editor | **not from the font**: `round(1.5 × fontSize)` on macOS, `round(1.35 × fontSize)` elsewhere, unless the user sets `lineHeight` | [fontInfo.ts](https://raw.githubusercontent.com/microsoft/vscode/main/src/vs/editor/common/config/fontInfo.ts) |
| Skia (Chrome on Linux/Android) | bit 7 set → sTypo; else FreeType's values | [SkFontHost_FreeType.cpp](https://raw.githubusercontent.com/google/skia/main/src/ports/SkFontHost_FreeType.cpp) |
| Skia (Chrome on Windows) | `DWRITE_FONT_METRICS` ascent / descent / lineGap | [SkScalerContext_win_dw.cpp](https://raw.githubusercontent.com/google/skia/main/src/ports/SkScalerContext_win_dw.cpp) |
| Blink layout | ascent and descent are each rounded to whole pixels; `line spacing = lround(ascent) + lround(descent) + lround(line_gap)` | [font_metrics.cc](https://raw.githubusercontent.com/chromium/chromium/main/third_party/blink/renderer/platform/fonts/font_metrics.cc), [simple_font_data.cc](https://raw.githubusercontent.com/chromium/chromium/main/third_party/blink/renderer/platform/fonts/simple_font_data.cc) |
| Gecko (FreeType) | line height from sTypo asc − desc + gap when sTypoAscender is non-zero; max ascent/descent from sTypo only when bit 7 is set, else hhea; every component rounded to whole pixels | [gfxFT2FontBase.cpp](https://raw.githubusercontent.com/mozilla-firefox/firefox/main/gfx/thebes/gfxFT2FontBase.cpp) |
| CSS specification | recommends sTypoAscender / sTypoDescender, falling back to hhea; "UAs must floor the line gap metric at zero" | [CSS Inline Layout 3 §3.2](https://www.w3.org/TR/css-inline-3/#ascent-descent) |
| DirectWrite | "recommended line spacing … is the sum of ascent, descent, and lineGap"; the page does not say which font tables feed them | [DWRITE_FONT_METRICS](https://learn.microsoft.com/en-us/windows/win32/api/dwrite/ns-dwrite-dwrite_font_metrics) |
| macOS | "Hhea metrics are used in macOS" | [GF guide](https://googlefonts.github.io/gf-guide/metrics.html) |

### Consequences

1. **[inference]** If hhea = typo = win (with win sign flipped), both gaps 0, and bit 7 set, then every rule in the table reduces to the same unscaled number `asc − desc`. No consumer has to choose between tables, so the unknown DirectWrite mapping stops mattering. This is the spec's "alternative guidance" and satisfies every GF rule provided no glyph exceeds [descender, ascender], because then yMax = ascender and yMin = descender.
2. **[inference]** That proviso constrains the drawing: box-drawing, block and Powerline glyphs must span exactly [descender, ascender] to join across lines, and nothing (stacked accents, tall brackets, overshoot of box glyphs) may go beyond. If something must go beyond, raise only `usWinAscent/Descent` to the new bbox: bit-7-aware consumers are unaffected; GDI-era ones get taller lines.
3. **[inference]** Pixel line height still differs by ±1 px between consumers at most sizes, because they round differently (kitty `ceil`, Ghostty and Windows Terminal `round`, Alacritty `floor`, Blink rounds ascent and descent separately). It is identical only where `asc × ppem / UPM` and `desc × ppem / UPM` are both integers. Computed examples (ppem → ceil / round / floor / Blink):

   | Metrics (UPM 1000) | 12 | 13 | 14 | 15 | 16 | 20 | 24 |
   |---|---|---|---|---|---|---|---|
   | 975 / −275 (1.25 em, caps centred for cap height 700) | 15/15/15/15 | 17/16/16/17 | 18/18/17/18 | 19/19/18/19 | 20/20/20/20 | 25/25/25/**26** | 30/30/30/30 |
   | 950 / −250 (1.20 em) | 15/14/14/14 | 16/16/15/15 | 17/17/16/17 | 18/18/18/18 | 20/19/19/19 | 24/24/24/24 | 29/29/28/29 |
   | 1000 / −300 (1.30 em) | 16/16/15/16 | 17/17/16/17 | 19/18/18/18 | 20/20/19/20 | 21/21/20/21 | 26/26/26/26 | 32/31/31/31 |

   With asc and desc both multiples of UPM/4 (e.g. 1000 / −250, total 1.25 em) all four rules agree at every ppem divisible by 4 (12, 16, 20, 24, 28, 32).
4. The same applies to cell width: at 0.6 em the advance is integral only at ppem divisible by 5 (16 px → 9.6: kitty/Ghostty/Windows Terminal give 10, Alacritty 9); at 0.625 em it is integral at ppem divisible by 8 (16 → 10, 24 → 15); at 0.5 em at every even ppem. **[inference from the rounding rules above]**
5. For hinted fonts, ttfautohint "tends to slightly increase the vertical glyph dimensions at smaller sizes", by less than 1 px per edge, and advises leaving padding rather than tight win values — [ttfautohint docs, `--windows-compatibility`](https://freetype.org/ttfautohint/doc/ttfautohint.html).

---

## (c) Naming, style linking, and the two variable fonts

### Static family: exact table

The spec rule: name IDs 1/2 form groups of at most four style-linked faces (regular, italic, bold, bold italic); everything else goes into ID 1, with IDs 16/17 carrying the real family and style ([name spec, IDs 1, 2, 16, 17](https://learn.microsoft.com/en-us/typography/opentype/spec/name#name-ids)). `fsSelection` bit 0 must equal `macStyle` bit 1, bit 5 must equal `macStyle` bit 0, and bit 6 excludes bits 0 and 5 ([OS/2 fsSelection](https://learn.microsoft.com/en-us/typography/opentype/spec/os2#fsselection)). GF's table for these styles is at [GF guide, Static fonts](https://googlefonts.github.io/gf-guide/statics.html).

**[measured]** The values below are what fontmake produced from designspace `<instance>` elements carrying `stylemapfamilyname` / `stylemapstylename`, with `openTypeOS2Selection=[7]` in the masters ("Family" stands for the family name; `fsSelection` includes bit 7):

| File | ID 1 | ID 2 | ID 4 | ID 6 | ID 16 | ID 17 | usWeightClass | fsSelection | macStyle |
|---|---|---|---|---|---|---|---|---|---|
| Family-Light.ttf | Family Light | Regular | Family Light | Family-Light | Family | Light | 300 | 0x00C0 | 0 |
| Family-Regular.ttf | Family | Regular | Family Regular | Family-Regular | — | — | 400 | 0x00C0 | 0 |
| Family-Medium.ttf | Family Medium | Regular | Family Medium | Family-Medium | Family | Medium | 500 | 0x00C0 | 0 |
| Family-SemiBold.ttf | Family SemiBold | Regular | Family SemiBold | Family-SemiBold | Family | SemiBold | 600 | 0x00C0 | 0 |
| Family-Bold.ttf | Family | Bold | Family Bold | Family-Bold | — | — | 700 | 0x00A0 | 1 |
| Family-LightItalic.ttf | Family Light | Italic | Family Light Italic | Family-LightItalic | Family | Light Italic | 300 | 0x0081 | 2 |
| Family-Italic.ttf | Family | Italic | Family Italic | Family-Italic | — | — | 400 | 0x0081 | 2 |
| Family-MediumItalic.ttf | Family Medium | Italic | Family Medium Italic | Family-MediumItalic | Family | Medium Italic | 500 | 0x0081 | 2 |
| Family-SemiBoldItalic.ttf | Family SemiBold | Italic | Family SemiBold Italic | Family-SemiBoldItalic | Family | SemiBold Italic | 600 | 0x0081 | 2 |
| Family-BoldItalic.ttf | Family | Bold Italic | Family Bold Italic | Family-BoldItalic | — | — | 700 | 0x00A1 | 3 |

How ufo2ft derives these ([outlineCompiler.py `setupTable_name`, `setupTable_OS2`, `setupTable_head`](https://github.com/googlefonts/ufo2ft/blob/main/Lib/ufo2ft/outlineCompiler.py), [fontInfoData.py](https://github.com/googlefonts/ufo2ft/blob/main/Lib/ufo2ft/fontInfoData.py)):

- ID 1 = `styleMapFamilyName`; ID 2 = `styleMapStyleName.title()`; ID 16/17 = `openTypeNamePreferredFamilyName/SubfamilyName` (fallback `familyName` / `styleName`), dropped when both equal IDs 1/2.
- ID 4 = "preferredFamily preferredSubfamily". ID 6 = `postscriptFontName`, fallback "Family-Style" with spaces removed. ID 3 = "version;vendorID;postscriptName" (e.g. `1.000;NONE;Testmono-Regular`). ID 5 = "Version M.mmm".
- `styleMapStyleName` adds `fsSelection` bit 6 / 5 / 0 / 0+5 and `macStyle` bits; `openTypeOS2Selection` supplies the other bits. The UFO spec forbids putting bits 0, 5, 6 into `openTypeOS2Selection` ([UFO fontinfo](https://unifiedfontobject.org/versions/ufo3/fontinfo.plist/)).
- Only Windows records (3, 1, 0x409) are written. GF: "fontmake doesn't produce Mac name entries any more" ([statics guide](https://googlefonts.github.io/gf-guide/statics.html)); fontbakery's `no_mac_entries` fails if any exist.
- ID 6 limits: ≤ 63 characters, printable ASCII 33–126 except `[ ] ( ) { } < > / %` ([name spec, ID 6](https://learn.microsoft.com/en-us/typography/opentype/spec/name#name-ids)).

`usWeightClass`: 300 Light, 400 Regular, 500 Medium, 600 Semi-bold, 700 Bold ([OS/2 usWeightClass](https://learn.microsoft.com/en-us/typography/opentype/spec/os2#usweightclass)). **[measured]** fontmake set it per instance from the `wght` user location.

Italic angle and caret:

- `post.italicAngle`: "counter-clockwise degrees from the vertical … negative for text that leans to the right" ([post spec](https://learn.microsoft.com/en-us/typography/opentype/spec/post)).
- `hhea.caretSlopeRise/Run`: "1 for vertical" / "0 for vertical"; `caretOffset` 0 for non-slanted ([hhea spec](https://learn.microsoft.com/en-us/typography/opentype/spec/hhea)).
- ufo2ft fallbacks: upright → rise = UPM, run = 0; italic → rise = UPM, run = `otRound(tan(radians(−italicAngle)) × rise)` ([fontInfoData.py](https://github.com/googlefonts/ufo2ft/blob/main/Lib/ufo2ft/fontInfoData.py)). **[measured]** `italicAngle = −10` → rise 1000, run 176.
- fontbakery `opentype/caret_slope` WARNs if the caret angle differs from `italicAngle` by more than 0.1°, FAILs on rise 0; `opentype/italic_angle` FAILs if an italic has angle 0 or an upright has a non-zero angle, WARNs above 20° ([caret_slope.py](https://github.com/fonttools/fontbakery/blob/main/Lib/fontbakery/checks/opentype/caret_slope.py), [italic_angle.py](https://github.com/fonttools/fontbakery/blob/main/Lib/fontbakery/checks/opentype/italic_angle.py)). The latter measures the real slant from `|`, `[`, `H`, `I` at 20 % and 80 % of their height.

`fsSelection` bit 8 (WWS): the spec says it "should be set" when a face differs within its family only by weight, width or slope ([OS/2 fsSelection](https://learn.microsoft.com/en-us/typography/opentype/spec/os2#fsselection)); gftools' fixer clears every bit except 7 before setting 0/5/6 ([gftools fix.py `fix_fs_selection`](https://github.com/googlefonts/gftools/blob/main/Lib/gftools/fix.py)). fontbakery checks neither way.

Static fonts need a STAT table too when uprights and italics ship together: **[measured]** `opentype/STAT/ital_axis` FAILed with `no-stat` on the 10 static TTFs, and passed after adding a STAT with exactly one `wght` value and one `ital` value per file. `STAT_in_statics` FAILs if a static carries more than one value per axis ([source](https://github.com/fonttools/fontbakery/blob/main/Lib/fontbakery/checks/STAT_in_statics.py)). `fontTools.otlLib.builder.buildStatTable(ttFont, axes, locations=None, elidedFallbackName=2, windowsNames=True, macNames=True)` adds Macintosh name records by default; **[measured]** that made `no_mac_entries` FAIL until `macNames=False` was passed.

### Upright + italic variable pair

Requirements:

- A STAT table "is required in all variable fonts" ([STAT spec](https://learn.microsoft.com/en-us/typography/opentype/spec/stat)).
- `wght`: range 1–1000, "400 is required" as the Regular value, and `OS/2.usWeightClass` "must match the default 'wght' value specified in the 'fvar' table" ([wght axis](https://learn.microsoft.com/en-us/typography/opentype/spec/dvaraxistag_wght)).
- `ital`: 0 = roman (required Regular value), 1 = italic; "used within a STAT table of italic fonts"; should not be combined with `slnt` ([ital axis](https://learn.microsoft.com/en-us/typography/opentype/spec/dvaraxistag_ital)).
- fvar: an instance record for the default instance should use name ID 2 or 17 (and 6 for the PostScript name); all records distinct ([fvar spec](https://learn.microsoft.com/en-us/typography/opentype/spec/fvar)).
- STAT format 3 `linkedValue` is the "bold" link (400 → 700) and the roman → italic link (0 → 1); `ELIDABLE_AXIS_VALUE_NAME` (0x0002) marks "Regular" ([STAT spec, examples 1–2](https://learn.microsoft.com/en-us/typography/opentype/spec/stat)).
- GF ([variable guide](https://googlefonts.github.io/gf-guide/variable.html)): file names `Family[wght].ttf` and `Family-Italic[wght].ttf`; `ital` only as a STAT value linking two files ("GF doesn't support the ital axis within one VF"); `wght` range must include 400; named instances only Thin…Black (+ Italic) at multiples of 100; `wght` and `ital` last in STAT; no format 2; the default location names the font ("the font origin will be the actual default instance"); name ID 25 must differ between roman and italic.
- Name ID 25: characters restricted to ASCII letters and digits ([name spec, ID 25](https://learn.microsoft.com/en-us/typography/opentype/spec/name#name-ids)); it is the family prefix in Adobe's algorithm, to which "-" + instance subfamily name is appended ([Adobe TN #5902](https://adobe-type-tools.github.io/font-tech-notes/pdfs/5902.AdobePSNameGeneration.pdf)). GF builds it as family name without spaces, plus "Italic" for the italic file ([axisregistry `build_variations_ps_name`](https://github.com/googlefonts/axisregistry/blob/main/Lib/axisregistry/__init__.py)); fontbakery `googlefonts/metadata/valid_nameid25` FAILs an italic VF whose ID 25 does not end in "Italic".
- fontbakery `opentype/STAT/ital_axis`: `ital` must be the last STAT axis; upright value 0.0 with flags 0x0002 and linkedValue 1.0; italic value 1.0 with flags 0 ([ital_axis.py](https://github.com/fonttools/fontbakery/blob/main/Lib/fontbakery/checks/opentype/STAT/ital_axis.py)).

**[measured]** One designspace (format 5) with a continuous `wght` axis (300–700, default 400), a **discrete** `ital` axis (values 0 and 1), `<labels>` on both axes and two `<variable-font>` elements named `Testmono[wght]` and `Testmono-Italic[wght]` built, in a single `fontmake -m X.designspace -o variable` run:

| | `Testmono[wght].ttf` | `Testmono-Italic[wght].ttf` |
|---|---|---|
| IDs 1 / 2 / 4 / 6 | Testmono / Regular / Testmono Regular / Testmono-Regular | Testmono / Italic / Testmono Italic / Testmono-Italic |
| IDs 16 / 17 | absent | absent |
| `fvar` axis | wght 300 / 400 / 700 | wght 300 / 400 / 700 |
| `fvar` instances (name, wght, PS name) | Light 300 Testmono-Light; Regular 400 (reuses name ID 2) Testmono-Regular; Medium 500; SemiBold 600; Bold 700 | Light Italic 300 Testmono-LightItalic; Italic 400 (name ID 2); Medium Italic 500; SemiBold Italic 600; Bold Italic 700 |
| STAT axes | wght (ordering 0), ital (ordering 1) | same |
| STAT values | Light 300; Regular 400 fmt 3, flags 2, linked 700; Medium 500; SemiBold 600; Bold 700; Roman ital 0 fmt 3, flags 2, linked 1 | same wght values; Italic ital 1 fmt 1, flags 0 |
| STAT elidedFallbackNameID | 2 ("Regular") | 2 ("Italic") |
| usWeightClass / fsSelection / macStyle | 400 / 0x00C0 / 0 | 400 / 0x0081 / 2 |
| italicAngle, caret rise/run | 0, 1000/0 | −10, 1000/176 |
| Variation tables | fvar, gvar, HVAR, STAT (no avar, no MVAR) | same |

Details:

- STAT comes from the designspace labels: `varLib.build_many` calls `buildVFStatTable` only when the document is format ≥ 5.0 and has axis labels, axis ordering or location labels; otherwise the STAT has axis records and no values ([fontTools varLib `build_many`](https://github.com/fonttools/fonttools/blob/main/Lib/fontTools/varLib/__init__.py), [varLib/stat.py](https://github.com/fonttools/fonttools/blob/main/Lib/fontTools/varLib/stat.py)).
- fvar instance PostScript names come from the instance `postscriptfontname`; the default-location instance reuses name ID 2/17 ([varLib `_add_fvar`](https://github.com/fonttools/fonttools/blob/main/Lib/fontTools/varLib/__init__.py)).
- **Name ID 25 is not generated.** **[measured]** absent after fontmake; adding `openTypeNameRecords = [{nameID: 25, platformID: 3, encodingID: 1, languageID: 0x409, string: "TestmonoItalic"}]` to the default italic master (and "Testmono" to the default upright master) put it into the VFs via `ufo2ft.compileVariableTTFs`, and the GF check then passed.
- avar: fontTools logged "No need for avar" for the linear 300/400/700 mapping; fontbakery `mandatory_avar_table` WARNs on its absence but its own rationale says "If the progression rates of axes is linear, this check can be ignored" ([source](https://github.com/fonttools/fontbakery/blob/main/Lib/fontbakery/checks/mandatory_avar_table.py)). GF recommends an avar when instances are not evenly spaced in design space; the designspace `<map input= output=>` elements create it ([GF variable guide](https://googlefonts.github.io/gf-guide/variable.html)).
- MVAR appears only if metrics differ between masters; keeping vertical metrics, underline and strikeout identical in every master keeps it out. **[measured]** no MVAR.
- `varLib.set_default_weight_width_slant` overwrites `usWeightClass` with the default `wght` value ([varLib](https://github.com/fonttools/fonttools/blob/main/Lib/fontTools/varLib/__init__.py)).
- `ufo2ft.compileVariableTTFs(designSpaceDoc)` returns a dict keyed by variable-font name, so the Python build program can call it directly instead of the CLI. **[measured]**

fontbakery `check-universal` on the two VFs: no FAIL attributable to the build (the one FAIL, `case_mapping`, came from my test glyph set lacking U+00E0); WARN `mandatory_avar_table`, WARN `bad-numberOfHMetrics`. **[measured]**

---

## (d) Outlines

### Direction and fill rule

- TrueType: "if the curve is followed in the direction of increasing point numbers, the black space (the filled area) will always be to the right" (outer contours clockwise), and the scan converter uses the non-zero winding number rule ([TrueType fundamentals](https://learn.microsoft.com/en-us/typography/opentype/spec/ttch01)).
- PostScript/CFF: "A subpath that is to be filled must be defined in a counterclockwise orientation … a filled area should be on your left" ([Adobe Type 1 Font Format §3.5](https://adobe-type-tools.github.io/font-tech-notes/pdfs/T1_SPEC.pdf)).
- ufo2ft assumes UFO contours follow the PostScript convention and reverses them for TrueType output; `reverseDirection=True` is the default and the CFF path does not reverse ([preProcessor.py `TTFPreProcessor`](https://github.com/googlefonts/ufo2ft/blob/main/Lib/ufo2ft/preProcessor.py), [ttfCompiler.py](https://github.com/googlefonts/ufo2ft/blob/main/Lib/ufo2ft/_compilers/ttfCompiler.py)). fontmake's `--keep-direction` disables the reversal.
- **[measured]** Two overlapping rectangles drawn counter-clockwise in the UFO: `removeOverlaps=True` → 1 contour, area 110 000 units² (the union); kept overlaps → FreeType fills the union (1100 px² at 100 ppem). With the second rectangle clockwise: both overlap backends return 2 contours with area 100 000 (the intersection becomes a hole), and with overlaps kept FreeType leaves the intersection empty (1000 px²). **Every stroke outline must therefore have the same orientation**, counter-clockwise in the UFO; a mixed-direction overlap is a hole in statics and in the VF alike.
- fontbakery `outline_direction` (googlefonts profile, TTF only) WARNs on a counter-clockwise outermost contour ([source](https://github.com/fonttools/fontbakery/blob/main/Lib/fontbakery/checks/outline_direction.py)).

### Overlaps

- Variable fonts keep overlaps; the `glyf` spec: `OVERLAP_SIMPLE` (bit 6 of the first flag byte) "is not required", but "may be (and is) used by some rasterizers to activate additional logic required when contours overlap"; a tool deriving static instances "should either set the OVERLAP_SIMPLE flag … or else should merge contours". `OVERLAP_COMPOUND` (bit 10 of the first component's flags) is the composite equivalent ([glyf spec](https://learn.microsoft.com/en-us/typography/opentype/spec/glyf)). fontTools states the reason: "some font rendering engines on Apple platforms require that the OVERLAP_SIMPLE and OVERLAP_COMPOUND flags … be set to force rendering using a non-zero fill rule" ([varLib/instancer](https://github.com/fonttools/fonttools/blob/main/Lib/fontTools/varLib/instancer/__init__.py)).
- **fontmake 3.12.2 has no command-line option that sets the flag.** Its contour options are `--keep-overlaps`, `--overlaps-backend {booleanOperations,pathops}`, `--keep-direction`, `--ttf-curves`, `-e/--conversion-error`, `-f/--flatten-components` (output of `fontmake --help`). The mechanism is the per-glyph UFO lib key `public.truetype.overlap` (boolean; [UFO glif spec](https://unifiedfontobject.org/versions/ufo3/glyphs/glif/)), which ufo2ft maps to `OVERLAP_SIMPLE` on simple glyphs and `OVERLAP_COMPOUND` on the first component ([instructionCompiler.py](https://github.com/googlefonts/ufo2ft/blob/main/Lib/ufo2ft/instructionCompiler.py)). **[measured]** With the key set on every glyph that has more than one contour or any component, the VF had the flag on 93 of 99 simple glyphs and on its 1 composite; without the key, 0.
- `fonttools varLib.instancer` sets both flags on all glyphs when producing a full static instance unless `--no-overlap-flag`; `--remove-overlaps` merges instead (needs skia-pathops) ([instancer](https://github.com/fonttools/fonttools/blob/main/Lib/fontTools/varLib/instancer/__init__.py)).
- Statics: fontmake removes overlaps by default (`remove_overlaps=True`; `--keep-overlaps` turns it off); ufo2ft's own default is `removeOverlaps=False`; the default backend is booleanOperations, `pathops` selects skia-pathops ([removeOverlaps.py](https://github.com/googlefonts/ufo2ft/blob/main/Lib/ufo2ft/filters/removeOverlaps.py), [baseCompiler.py](https://github.com/googlefonts/ufo2ft/blob/main/Lib/ufo2ft/_compilers/baseCompiler.py)). Interpolatable/variable outputs never have overlaps removed.
- Type 1 guidance for CFF: "A single closed outline should not intersect itself"; overlapping subpaths fill correctly but show when stroked ([T1 spec §3.6](https://adobe-type-tools.github.io/font-tech-notes/pdfs/T1_SPEC.pdf)).

### Curves, rounding, components

- cu2qu tolerance: default `DEFAULT_MAX_ERR = 0.001` em, i.e. the maximum distance between the cubic and its quadratic approximation is 1 unit at 1000 UPM ([fontTools cu2qu/ufo.py](https://github.com/fonttools/fonttools/blob/main/Lib/fontTools/cu2qu/ufo.py), [ufo2ft cubicToQuadratic.py](https://github.com/googlefonts/ufo2ft/blob/main/Lib/ufo2ft/filters/cubicToQuadratic.py)); set with `fontmake -e ERROR` ("measured in EM") or `cubicConversionError=`. For variable builds all masters are converted together so point counts stay compatible ([preProcessor.py `TTFInterpolatablePreProcessor`](https://github.com/googlefonts/ufo2ft/blob/main/Lib/ufo2ft/preProcessor.py)).
- `--ttf-curves keep-quad` skips cu2qu when the UFO already holds quadratic curves; `mixed`/`keep-cubic` write `glyf` format 1, described in the help text as "still draft".
- Integer coordinates: static TTF glyphs are rounded with `otRound`; interpolatable masters keep floats (`roundCoordinates=False`) and varLib rounds when building the VF; CFF rounds everything by default (`roundTolerance=0.5`; `--cff-round-tolerance 0` disables) ([outlineCompiler.py](https://github.com/googlefonts/ufo2ft/blob/main/Lib/ufo2ft/outlineCompiler.py), [interpolatableTTFCompiler.py](https://github.com/googlefonts/ufo2ft/blob/main/Lib/ufo2ft/_compilers/interpolatableTTFCompiler.py)). Advance widths are `otRound`ed and a negative width raises `ValueError`.
- Extrema: no ufo2ft or fontmake step adds extreme points (none among the default filters in [preProcessor.py](https://github.com/googlefonts/ufo2ft/blob/main/Lib/ufo2ft/preProcessor.py)). The Type 1 spec asks for them: "An endpoint … should be placed at most horizontal or vertical extremes. This implies that most curves should not include more than 90 degrees of arc" ([T1 spec §4.1](https://adobe-type-tools.github.io/font-tech-notes/pdfs/T1_SPEC.pdf)); ttfautohint's algorithm "is to identify horizontal segments at extremum positions, especially for blue zones" ([ttfautohint docs](https://freetype.org/ttfautohint/doc/ttfautohint.html)). The generator has to emit them.
- Components: the CFF path decomposes everything; the TTF path keeps pure composites and decomposes only glyphs mixing contours and components or with a 2×2 transform outside [−2, 2] ([preProcessor.py](https://github.com/googlefonts/ufo2ft/blob/main/Lib/ufo2ft/preProcessor.py)).
- **[measured] build trap**: `fontmake … -o ttf otf` in one invocation produced TTFs whose composites were decomposed (Àgrave: 2 contours, not composite), while `-o ttf` alone kept the composite. fontmake compiles with `inplace=True`, so the two formats share the preprocessed glyphs. Build each format in its own invocation, or call ufo2ft with a fresh UFO per format.
- `.notdef`: ufo2ft synthesises a box glyph with advance `UPM × 0.5` if the UFO has none ([outlineCompiler.py `makeMissingRequiredGlyphs`](https://github.com/googlefonts/ufo2ft/blob/main/Lib/ufo2ft/outlineCompiler.py)); at 1000 UPM that is 500, which would be a second advance width in a 600-unit font. Glyph 0 must be `.notdef` and should be a visible box ([recom](https://learn.microsoft.com/en-us/typography/opentype/spec/recom#glyph-0-the-notdef-glyph)).

---

## (e) Hinting

### TrueType statics: ttfautohint

From the [ttfautohint documentation](https://freetype.org/ttfautohint/doc/ttfautohint.html):

- It does no horizontal hinting: "Since ttfautohint doesn't do any horizontal hinting, those tables [LTSH, hdmx] are superfluous and thus removed". **[measured]** every advance was unchanged after hinting, `numberOfHMetrics` and `isFixedPitch` unchanged.
- It replaces `cvt`, `prep`, `fpgm` and all glyph programs, and sets `gasp` "to always use grayscale rendering, for all sizes, with grid-fitting for standard hinting, and symmetric grid-fitting and symmetric smoothing". **[measured]** `gasp = {0xFFFF: 0x000F}`; the new `prep` still contains the smart-dropout sequence; size 6992 → 14 996 bytes for 102 glyphs.
- `--stem-width-mode` / `-a`: three letters for grayscale, GDI ClearType, DirectWrite ClearType; `n` natural ("No adjustments to stem widths … what FreeType uses for its 'light' (auto-)hinting mode. Essentially no glyph shape distortion, low contrast"), `q` quantized, `s` strong; default `qsq`.
- `--reference FILE`: "Derive all blue zones from the given font … Use this to harmonize font families, avoiding ugly height differences at small sizes".
- `--increase-x-height` default 14 (0 disables); `--hinting-range-min/max` (library defaults 8 / 50); `--hinting-limit` default 200; `--fallback-stem-width` default 50 units at 2048 UPM ≈ 24 at 1000; `--windows-compatibility` adds blue zones at `usWinAscent/Descent`; `--no-info` keeps name ID 5 untouched, otherwise "; ttfautohint (vNNN)" is appended (**[measured]** "Version 1.000; ttfautohint (v1.8.4.16-eb64)").
- The CLI "honours the SOURCE_DATE_EPOCH environment variable for reproducible builds. This corresponds to the new library option epoch".
- The documentation does not mention variable fonts at all.

ttfautohint-py usage **[measured]**: `from ttfautohint import ttfautohint, StemWidthMode`; `ttfautohint(in_file=…, out_file=…, no_info=True, gray_stem_width_mode=StemWidthMode.NATURAL, gdi_cleartype_stem_width_mode=StemWidthMode.STRONG, dw_cleartype_stem_width_mode=StemWidthMode.NATURAL, hinting_range_min=6, hinting_range_max=50, increase_x_height=0, reference_file=…)`. The CLI's `stem_width_mode="nsn"` string is not accepted (`TypeError: unknown keyword argument`). Two runs 2 s apart differ unless `epoch=` is passed or `SOURCE_DATE_EPOCH` is in the environment (both verified identical).

After ttfautohint, `head.flags` went 0x0003 → 0x0007 **[measured]**; bit 3 ("Force ppem to integer values … strongly recommended that this be set in hinted fonts", [head spec](https://learn.microsoft.com/en-us/typography/opentype/spec/head)) is not set, and fontbakery `integer_ppem_if_hinted` FAILed until it is. gftools' fix is `head.flags |= 1 << 3` ([fix.py `fix_hinted_font`](https://github.com/googlefonts/gftools/blob/main/Lib/gftools/fix.py)).

fontmake's `-a/--autohint [ARGS]` runs ttfautohint on TTF output; by default it only runs for Glyphs sources carrying a "TTFAutohint options" parameter (`fontmake --help`).

### gasp and prep for unhinted TrueType (the VF, and statics if left unhinted)

- `gasp` flags: 0x0001 GRIDFIT, 0x0002 DOGRAY, 0x0004 SYMMETRIC_GRIDFIT, 0x0008 SYMMETRIC_SMOOTHING; version 1 for new fonts ([gasp spec](https://learn.microsoft.com/en-us/typography/opentype/spec/gasp)).
- gftools for unhinted fonts writes `gasp = {0xFFFF: 15}` and a `prep` of `PUSHW 511; SCANCTRL; PUSHB 4; SCANTYPE` ([fix.py `fix_unhinted_font`](https://github.com/googlefonts/gftools/blob/main/Lib/gftools/fix.py)). fontbakery `smart_dropout` FAILs a TTF whose `prep` lacks the bytes `b8 01 ff 85 b0 04 8d` ([source](https://github.com/fonttools/fontbakery/blob/main/Lib/fontbakery/checks/smart_dropout.py)); `googlefonts/gasp` wants a single 0xFFFF range with value 0x0F ([source](https://github.com/fonttools/fontbakery/blob/main/Lib/fontbakery/checks/vendorspecific/googlefonts/gasp.py)). The GF guide's prose says 0x000A for unhinted fonts ([statics guide](https://googlefonts.github.io/gf-guide/statics.html)); the tool and the check say 0x000F.
- **[measured]** Both tables can come straight from the UFO, no post-processing: `info.openTypeGaspRangeRecords = [{"rangeMaxPPEM": 65535, "rangeGaspBehavior": [0, 1, 2, 3]}]` and `lib["public.truetype.instructions"] = {"formatVersion": "1", "controlValueProgram": "PUSHW[ ] 511\nSCANCTRL[ ]\nPUSHB[ ] 4\nSCANTYPE[ ]"}` gave `gasp {65535: 0xF}` (version 1) and `prep = b801ff85b0048d` in statics and in both VFs; `smart_dropout` passed.
- That `prep` is exactly 7 bytes, and FreeType falls back to its auto-hinter for a TrueType font when `font_program_size == 0 && cvt_program_size <= 7` ([ftobjs.c](https://raw.githubusercontent.com/freetype/freetype/master/src/base/ftobjs.c)). So the unhinted-font `prep` does not switch FreeType's auto-hinter off.

### What unhinted TrueType looks like

- FreeType: since 2.7 the v40 interpreter is the default and "snaps glyphs to the pixel grid mainly or only vertically"; "light" hinting "snaps glyphs to the pixel grid only vertically … preserves inter-glyph spacing" and uses the auto-hinter when the font has no native hints ([FreeType: subpixel hinting](https://freetype.org/freetype2/docs/hinting/subpixel-hinting.html), [text rendering](https://freetype.org/freetype2/docs/hinting/text-rendering-general.html)). An unhinted TTF therefore gets auto-hinted vertically wherever the application enables hinting, and is drawn as pure antialiased outlines where it does not.
- Windows: GF's position is "ttfautohint … If the results look poor on Windows browsers, it's better to release the fonts unhinted with GASP table set to 'grayscale / symmetric smoothing'" ([statics guide](https://googlefonts.github.io/gf-guide/statics.html)). ClearType's backward-compatible mode deliberately weakens x-direction instructions ([Microsoft, TrueType and ClearType](https://learn.microsoft.com/en-us/typography/cleartype/truetypecleartype)).
- Chromium's source states "With DirectWrite or CoreText, no bytecode hinting is ever done" ([font_metrics.cc](https://raw.githubusercontent.com/chromium/chromium/main/third_party/blink/renderer/platform/fonts/font_metrics.cc)) — a code comment, not platform documentation.

### Variable fonts

GF: "the auto-hinting often results in a worse rendering than no hinting at all. That is why GF recommend to not hint variable fonts in general"; new families: "Fonts should be unhinted … Run fonts through gftools fix-nonhinting" ([variable guide, VF Hinting](https://googlefonts.github.io/gf-guide/variable.html)).

### CFF statics: blue zones, stems, otfautohint

- Type 1 / CFF Private dictionary rules ([T1 spec §5.3 ff.](https://adobe-type-tools.github.io/font-tech-notes/pdfs/T1_SPEC.pdf)): `BlueValues` is pairs of integers; the first pair is the baseline overshoot and the baseline (a bottom zone), all later pairs are top zones; at most 7 pairs; pairs at least 3 units apart (modifiable by BlueFuzz); `OtherBlues` holds further bottom zones (descender), at most 5 pairs. `StdHW` / `StdVW` are the dominant horizontal / vertical stem widths; `StemSnapH` / `StemSnapV` are up to 12 common widths in increasing order, and "For an italic font, [StemSnapV] should be empty".
- UFO keys and ufo2ft's mapping ([UFO fontinfo](https://unifiedfontobject.org/versions/ufo3/fontinfo.plist/), [outlineCompiler.py `setupTable_CFF`](https://github.com/googlefonts/ufo2ft/blob/main/Lib/ufo2ft/outlineCompiler.py)): `postscriptBlueValues` (≤ 14 numbers), `postscriptOtherBlues` (≤ 10), `postscriptFamilyBlues`, `postscriptFamilyOtherBlues`, `postscriptStemSnapH/V` (≤ 12), `postscriptBlueFuzz` (default 0), `postscriptBlueShift` (7), `postscriptBlueScale` (default `3 / (4 × tallest zone)`, or 0.039625 with no zones), `postscriptForceBold`. Blues are written only if at least one blues list is non-empty; stems only if **both** StemSnapH and StemSnapV are non-empty; `StdHW = stemSnapH[0]`, `StdVW = stemSnapV[0]` (first list element).
- **[measured]** `postscriptBlueValues=[-10,0,500,510,700,710]`, `postscriptOtherBlues=[-210,-200]`, `postscriptStemSnapH=[80]`, `postscriptStemSnapV=[80]` → CFF Private `BlueValues=[-10, 0, 500, 510, 700, 710]`, `OtherBlues=[-210, -200]`, `StdHW=80`, `StdVW=80`.
- Neither ufo2ft nor fontmake hints CFF glyphs: **[measured]** charstrings contained no stem operators. `otfautohint -o out.otf in.otf` (afdko) added them (`H` gained `hstemhm` / `hintmask`); file size 3168 → 9452 bytes because the output is not re-subroutinised. Its help says results "are better if the font's alignment zones are set properly … the baseline, the x-height and the capital height, and respective overshoots … at the very least", and it accepts variable CFF2 and UFO input (`otfautohint --info`, `--help`).
- psautohint is not installed by afdko 5.0.1; the command shipped is `otfautohint` **[measured from the installed package]**.

---

## (f) Reproducible builds

- fontTools: `timestampNow()` returns `SOURCE_DATE_EPOCH` (converted to the 1904 epoch) when the variable is set ([misc/timeTools.py](https://github.com/fonttools/fonttools/blob/main/Lib/fontTools/misc/timeTools.py), citing the [SOURCE_DATE_EPOCH specification](https://reproducible-builds.org/specs/source-date-epoch/)). `head.modified` is overwritten with it on **every** `TTFont.save()` while `recalcTimestamp` is true, which is the default ([_h_e_a_d.py `compile`](https://github.com/fonttools/fonttools/blob/main/Lib/fontTools/ttLib/tables/_h_e_a_d.py)).
- ufo2ft: `head.created` comes from `openTypeHeadCreated` ("YYYY/MM/DD HH:MM:SS"); its fallback is `SOURCE_DATE_EPOCH` if set, else now ([fontInfoData.py `openTypeHeadCreatedFallback`](https://github.com/googlefonts/ufo2ft/blob/main/Lib/ufo2ft/fontInfoData.py)).
- **[measured]** Full family build (2 VFs, 10 TTFs, 10 OTFs = 22 files), twice, with `SOURCE_DATE_EPOCH=1735689600` and `PYTHONHASHSEED` 1 vs 987654: all 22 files byte-identical; `head.created = head.modified = 3818534400` (= 1735689600 + 2 082 844 800). Without the variable, two builds a few seconds apart differed in all 22 files; the only differing table was `head` (`modified` 3877545819 vs 3877545824).
- **[measured]** Re-saving re-stamps: converting a finished TTF to WOFF2 through `TTFont.save()` without the variable changed `head.modified` to the current time (different file hash); with the variable it stayed 3818534400. Any post-processing step must either run under the same `SOURCE_DATE_EPOCH` or open the font with `recalcTimestamp=False`.
- ttfautohint: see (e) — `epoch` option or the environment variable; otherwise `head.modified` is "now" **[measured]**. Its default name-ID-5 suffix embeds the ttfautohint version, so pin the version or pass `no_info`.
- otfautohint under `SOURCE_DATE_EPOCH` kept `head.modified` **[measured]**.
- Remaining inputs to pin **[inference]**: exact versions of fontTools, ufo2ft, fontmake, cu2qu's compiled extension, booleanOperations/pyclipper or skia-pathops, compreffor/cffsubr, ttfautohint, brotli (WOFF2); the glyph order (`public.glyphOrder`, otherwise ufo2ft's own ordering); and floating-point determinism of our own outline generator. Name ID 3 embeds the version and PostScript name, not a date ([fontInfoData.py `openTypeNameUniqueIDFallback`](https://github.com/googlefonts/ufo2ft/blob/main/Lib/ufo2ft/fontInfoData.py)).

---

## (g) UFO keys that drive all of the above

### fontinfo.plist ([UFO 3 spec](https://unifiedfontobject.org/versions/ufo3/fontinfo.plist/); ufo2ft defaults from [fontInfoData.py](https://github.com/googlefonts/ufo2ft/blob/main/Lib/ufo2ft/fontInfoData.py))

| Key | Goes to | ufo2ft default if unset | Set to |
|---|---|---|---|
| `familyName`, `styleName` | fallbacks for IDs 16/17, PS name | "New Font" / "Regular" | family; "Light", "Italic", "SemiBold Italic", … |
| `styleMapFamilyName`, `styleMapStyleName` | name IDs 1, 2; `fsSelection` bits 0/5/6; `macStyle` | derived from family/style | per the table in (c); style is one of `regular`, `italic`, `bold`, `bold italic` |
| `openTypeNamePreferredFamilyName/SubfamilyName` | IDs 16/17 (omitted if equal to 1/2) | familyName / styleName | leave to fallback |
| `postscriptFontName`, `postscriptFullName` | ID 6; CFF FontName / FullName | "Family-Style" / "Family Style" | leave to fallback |
| `openTypeNameRecords` | arbitrary name records | `[]` | name ID 25 in the two default masters |
| `versionMajor`, `versionMinor` | `head.fontRevision` (3 decimals), ID 5 "Version M.mmm", ID 3 | 0, 0 | release version |
| `unitsPerEm` | `head.unitsPerEm` | 1000 | 1000 (or 2048) |
| `ascender`, `descender`, `xHeight`, `capHeight` | fallbacks; `OS/2.sxHeight`, `sCapHeight` | 0.8, −0.2, 0.5, 0.7 × UPM | design values |
| `italicAngle` | `post.italicAngle`, CFF ItalicAngle, caret fallback | 0 | 0 / negative angle |
| `openTypeHheaAscender/Descender/LineGap` | hhea | ascender + typoLineGap / descender / 0 | explicit, = typo |
| `openTypeHheaCaretSlopeRise/Run/Offset` | hhea | UPM, tan-derived, 0 | leave to fallback |
| `openTypeOS2TypoAscender/Descender/LineGap` | OS/2 | ascender / descender / max(1.2·UPM − asc + desc, 0) | explicit; gap 0 |
| `openTypeOS2WinAscent/Descent` | OS/2 (descent positive) | ascender + typoLineGap / abs(descender) | explicit, ≥ bbox |
| `openTypeOS2Selection` | `fsSelection` extra bits | `[]` | `[7]` (see (c) for bit 8) |
| `openTypeOS2WeightClass`, `WidthClass` | OS/2 | 400, 5 | 300/400/500/600/700; 5 |
| `openTypeOS2Panose` | OS/2 panose | ten zeros | `[2, 11, w, 9, …]` |
| `openTypeOS2Type` | `fsType` | `[2]` → fsType 4 **[measured]** | `[]` → fsType 0 (GF requires 0: [gftools `fix_fs_type`](https://github.com/googlefonts/gftools/blob/main/Lib/gftools/fix.py)) |
| `openTypeOS2VendorID` | `achVendID` | four spaces | a 4-character tag |
| `openTypeOS2UnicodeRanges`, `CodePageRanges` | OS/2 | recalculated from cmap | leave unset |
| `openTypeOS2StrikeoutSize/Position` | OS/2 | underline thickness / 0.6 × xHeight | explicit, equal in all masters |
| `openTypeHeadCreated` | `head.created` | SOURCE_DATE_EPOCH or now | fixed string, or rely on the variable |
| `openTypeHeadFlags` | `head.flags` | `[0, 1]` | `[0, 1]`; add 3 for hinted statics |
| `openTypeHeadLowestRecPPEM` | `head.lowestRecPPEM` | 6 | 6 |
| `openTypeGaspRangeRecords` | gasp (TTF only) | no table | `[{rangeMaxPPEM: 65535, rangeGaspBehavior: [0,1,2,3]}]` |
| `postscriptIsFixedPitch` | `post.isFixedPitch`, CFF | False | True |
| `postscriptUnderlinePosition/Thickness` | post, CFF | −0.075 × UPM / 0.05 × UPM | explicit, equal in all masters |
| `postscriptBlueValues`, `OtherBlues`, `FamilyBlues`, `FamilyOtherBlues`, `StemSnapH`, `StemSnapV`, `BlueFuzz`, `BlueShift`, `BlueScale`, `ForceBold` | CFF Private | empty / 0 / 7 / computed / 0 | see (e) |
| `copyright`, `trademark`, `openTypeNameDesigner`, `…DesignerURL`, `…Manufacturer`, `…ManufacturerURL`, `…License`, `…LicenseURL`, `…Description`, `…SampleText` | name IDs 0, 7–14, 19 | none | as appropriate |

Note on underline: the `post` field is "the top of the underline", whereas PostScript FontInfo uses its centre ([post spec](https://learn.microsoft.com/en-us/typography/opentype/spec/post)); ufo2ft writes `postscriptUnderlinePosition` unchanged into `post`.

### lib.plist and glyph lib keys

- `public.glyphOrder`: list of glyph names; ufo2ft uses it for the binary glyph order and always places `.notdef` first ([UFO lib spec](https://unifiedfontobject.org/versions/ufo3/lib.plist/), [outlineCompiler.py](https://github.com/googlefonts/ufo2ft/blob/main/Lib/ufo2ft/outlineCompiler.py)).
- `public.postscriptNames`: {glyph name: production name}. ufo2ft's post-processor renames glyphs when production names are enabled; without the mapping it derives `uniXXXX` / `uXXXXX` from the code point and keeps suffixes ([postProcessor.py](https://github.com/googlefonts/ufo2ft/blob/main/Lib/ufo2ft/postProcessor.py)). fontmake: `--production-names` / `--no-production-names`. TTF gets a `post` format 2 table with names, CFF a format 3 table (names live in the CFF) — [outlineCompiler.py](https://github.com/googlefonts/ufo2ft/blob/main/Lib/ufo2ft/outlineCompiler.py); **[measured]** post 2.0 / 3.0.
- `public.openTypeCategories`: {glyph name: `unassigned` | `base` | `ligature` | `mark` | `component`} → GDEF GlyphClassDef ([UFO lib spec](https://unifiedfontobject.org/versions/ufo3/lib.plist/), [gdefFeatureWriter.py](https://github.com/googlefonts/ufo2ft/blob/main/Lib/ufo2ft/featureWriters/gdefFeatureWriter.py)).
- `public.skipExportGlyphs`: glyphs to drop from the binary (decomposed where used as components).
- `public.truetype.instructions` (font lib: `controlValueProgram`, `fontProgram`, `controlValue`, …; glyph lib: per-glyph assembly), `public.truetype.overlap` (glyph lib), `public.truetype.useMyMetrics` / `roundOffsetToGrid` (component object libs) — [UFO glif spec](https://unifiedfontobject.org/versions/ufo3/glyphs/glif/), [instructionCompiler.py](https://github.com/googlefonts/ufo2ft/blob/main/Lib/ufo2ft/instructionCompiler.py).
- `public.openTypeMeta` → `meta` table; `public.unicodeVariationSequences` → cmap format 14; `com.github.googlei18n.ufo2ft.filters` and `…featureWriters` configure the pipeline ([constants.py](https://github.com/googlefonts/ufo2ft/blob/main/Lib/ufo2ft/constants.py)).
- cmap: ufo2ft writes format 4 subtables (0,3) and (3,1), plus format 12 (0,4) and (3,10) when any code point is above U+FFFF ([outlineCompiler.py `setupTable_cmap`](https://github.com/googlefonts/ufo2ft/blob/main/Lib/ufo2ft/outlineCompiler.py)).

### Automatic features

Default writers, in order: `CursFeatureWriter`, `KernFeatureWriter`, `MarkFeatureWriter`, `GdefFeatureWriter` ([featureCompiler.py](https://github.com/googlefonts/ufo2ft/blob/main/Lib/ufo2ft/featureCompiler.py)).

- **mark / mkmk** from anchors: an anchor whose name starts with `_` makes the glyph a mark and attaches to the same-named anchor without the underscore on bases; a mark that also has non-underscore anchors gets mark-to-mark; `top_1`, `top_2` address ligature components; `abvm`/`blwm` only for Indic/USE scripts; a feature already present in `features.fea` is skipped; anchor quantisation default 1 ([markFeatureWriter.py](https://github.com/googlefonts/ufo2ft/blob/main/Lib/ufo2ft/featureWriters/markFeatureWriter.py)).
- **GDEF**: GlyphClassDef from `public.openTypeCategories`; ligature carets from anchors named `caret_*` / `vcaret_*`; skipped if `features.fea` has its own GDEF block ([gdefFeatureWriter.py](https://github.com/googlefonts/ufo2ft/blob/main/Lib/ufo2ft/featureWriters/gdefFeatureWriter.py)). **[measured]** Without `public.openTypeCategories` the compiled font still had a GDEF with 94 base and 2 mark glyphs (the glyphs taking part in the mark feature); with it, 99 base and 2 mark. Only glyphs listed in the lib key or involved in mark lookups get a class.
- **kern** from `kerning.plist` / `groups.plist`; nothing is generated when they are empty ([kernFeatureWriter.py](https://github.com/googlefonts/ufo2ft/blob/main/Lib/ufo2ft/featureWriters/kernFeatureWriter.py)). **[measured]** no `kern` feature; fontbakery's `gpos_kerning_info` WARN appeared for the font without monospace metadata and not once `isFixedPitch`/PANOSE were set.
- For variable builds ufo2ft compiles "variable features" from the designspace (anchors become variable scalars); `--no-variable-features` reverts to per-master compilation merged by varLib (`fontmake --help`). **[measured]** log line "Compiling variable features for Testmono[wght]".
- `--debug-feature-file FILE` dumps the generated feature text.

---

## (h) fontbakery

### Which profile

fontbakery 1.1.0 subcommands: `check-opentype`, `check-universal`, `check-googlefonts`, `check-adobefonts`, `check-microsoft`, `check-notofonts`, `check-fontbureau`, `check-fontwerk`, `check-typenetwork`, `check-iso15008`, `check-fontval`, `check-profile` (`fontbakery --help`). `opentype` is the spec-conformance set; `universal` includes `opentype` and adds vendor-neutral good-practice checks ([profiles/universal.py](https://github.com/fonttools/fontbakery/blob/main/Lib/fontbakery/profiles/universal.py), [profiles/opentype.py](https://github.com/fonttools/fontbakery/blob/main/Lib/fontbakery/profiles/opentype.py)). For a font that is not going to Google Fonts, **`check-universal`** is the profile; `check-googlefonts` layers GF's publishing policy on top (METADATA.pb, description, glyph-set coverage, copyright wording, vendor ID registry) and needs `pip install "fontbakery[googlefonts]"` — without the extra it aborted with `ValueError: Check 'googlefonts/glyphsets/shape_languages' not found` **[measured]**.

fontbakery's README now points to [Fontspector](https://github.com/fonttools/fontspector), "the Rust port of Font Bakery", with built-in `opentype`, `universal` and `googlefonts` profiles ([fontbakery README](https://raw.githubusercontent.com/fonttools/fontbakery/main/README.md), [fontspector README](https://raw.githubusercontent.com/fonttools/fontspector/main/README.md)). I did not run Fontspector.

Useful flags: `--skip-network`, `-x CHECKID` to exclude, `-c CHECKID` to select, `--json FILE`, `-e FAIL|WARN` for the exit-code threshold, `--configuration FILE` (`fontbakery check-universal --help`).

### What fails for a programmatic font

**[measured]** `check-universal` on a UFO compiled with ufo2ft defaults (one TTF + one OTF):

| Result | Check | Cause | Fix |
|---|---|---|---|
| FAIL | `opentype/monospace` (`mono-bad-panose`, `mono-bad-post-isFixedPitch`) | defaults: PANOSE zeros, isFixedPitch False | `postscriptIsFixedPitch`, `openTypeOS2Panose` |
| ERROR | `opentype/monospace` on `.otf` | check reads `glyf` | none (fontbakery bug); test ourselves |
| FAIL | `os2_metrics_match_hhea` (`ascender`) | hhea 1000 vs typo 800 from fallbacks | set all nine metrics |
| FAIL | `family/win_ascent_and_descent` (`descent`) | fallback winDescent 200 < \|yMin\| 230 | win ≥ bbox |
| FAIL | `smart_dropout` (TTF) | no `prep` | `public.truetype.instructions` |
| WARN | `linegaps` | fallback sTypoLineGap 200 | gaps 0 |
| WARN | `typoascender_exceeds_Agrave` | typoAscender 800 < À | ascender ≥ tallest accented capital |
| WARN | `gpos_kerning_info` | no kerning and not flagged monospaced | flag as monospaced |
| WARN | `opentype/monospace` (`bad-numberOfHMetrics`) | 100 ≠ 3 | accept; see (a) |
| FAIL | `case_mapping`, WARN `contour_count` | my test glyph set (À without à; dummy shapes) | real glyph set; both are real risks for generated glyphs |

With the keys from (g) set, `check-universal` on 10 static TTFs + STAT, and on the 2 VFs, left only: FAIL `case_mapping` (test glyph set), WARN `contour_count` (dummy shapes), WARN `bad-numberOfHMetrics`, and on the VFs WARN `mandatory_avar_table`. Along the way these appeared and were fixed:

- FAIL `opentype/STAT/ital_axis` (`no-stat`) on statics → add a per-file STAT;
- FAIL `no_mac_entries` → `buildStatTable(..., macNames=False)`;
- FAIL `integer_ppem_if_hinted` after ttfautohint → `head.flags` bit 3;
- FAIL `opentype/family/bold_italic_unique_for_nameid1` when a TTF and an OTF of the same style are checked in one run → check each format separately.

`check-googlefonts` on the VFs additionally gave: FAIL `googlefonts/metadata/valid_nameid25` (fixed by name ID 25), FAIL `googlefonts/font_copyright` (wants "Copyright 2020 The Familyname Project Authors (git url)"), FAIL `googlefonts/glyph_coverage`, WARN `googlefonts/vendor_id` (unregistered tag), WARN `dotted_circle` (U+25CC missing while marks exist), WARN `googlefonts/meta/script_lang_tags` (no `meta` table).

Checks in the universal profile that generated outlines are most exposed to **[inference from the profile list and check sources]**: `contour_count` (expected contour counts per code point — unmerged strokes fail it in statics), `overlapping_path_segments`, `opentype/points_out_of_bounds`, `nested_components`, `transformed_components`, `interpolation_issues`, `whitespace_ink`, `whitespace_widths`, `math_signs_width`, `base_has_width`, `soft_hyphen`, `valid_glyphnames`, `unique_glyphnames`, `unreachable_glyphs`, `mandatory_glyphs`, `legacy_accents`, `tabular_kerning`, `empty_letters`, `ots`, `ttx_roundtrip`, `freetype_rasterizer`. The googlefonts profile adds `outline_alignment_miss`, `outline_colinear_vectors`, `outline_direction`, `outline_jaggy_segments`, `outline_semi_vertical`, `outline_short_segments` ([profiles/googlefonts.py](https://github.com/fonttools/fontbakery/blob/main/Lib/fontbakery/profiles/googlefonts.py)).

---

## What this means for our font

### Decisions

1. **Advances**: exactly two values in the whole font — the cell advance `W`, and 0 for combining marks. No double-width glyphs and no wide ligature glyphs. Give `.notdef` an explicit drawing with advance `W` (ufo2ft's synthetic one is `UPM/2`).
2. **Monospace metadata, in every master**: `postscriptIsFixedPitch = True`; `openTypeOS2Panose = [2, 11, weight, 9, 0, 0, 0, 0, 0, 0]`. Assert in our own test that `post.isFixedPitch == 1`, CFF `isFixedPitch == 1`, `panose.bProportion == 9`, `xAvgCharWidth == W`, `hhea.advanceWidthMax == W`, and that the set of advances is `{0, W}` — fontbakery cannot check the OTFs.
3. **Glyph order**: `.notdef`, then every zero-width glyph, then everything else, written to `public.glyphOrder`. Accept the `bad-numberOfHMetrics` WARN.
4. **Vertical metrics, identical in every master and style** (values are the engineering constraints; the design chooses A and D):
   - `openTypeHheaAscender = openTypeOS2TypoAscender = openTypeOS2WinAscent = A`
   - `openTypeHheaDescender = openTypeOS2TypoDescender = −D`, `openTypeOS2WinDescent = D`
   - `openTypeHheaLineGap = openTypeOS2TypoLineGap = 0`
   - `openTypeOS2Selection = [7]`
   - no glyph outside [−D, A]; box-drawing, block and Powerline glyphs span exactly [−D, A] and [0, W];
   - A ≥ top of the tallest accented capital (design the stacked accents to fit);
   - (A + D)/UPM between 1.2 and 1.3;
   - for exact agreement between `ceil`, `round`, `floor` and Blink at 12/16/20/24 px, make A and D multiples of UPM/4 (A = 1000, D = 250 at UPM 1000, 1.25 em); otherwise expect ±1 px between terminals at most sizes.
   Underline and strikeout position/thickness also identical in every master, so no MVAR is produced.
5. **Sources**: one designspace (format 5): continuous `wght` 300–700 with default 400 and a master at 400; discrete `ital` {0, 1}; `<labels>` — wght: Light 300, Regular 400 (elidable, linked 700), Medium 500, SemiBold 600, Bold 700; ital: Roman 0 (elidable, linked 1), Italic 1; `ital` after `wght`; two `<variable-font>` elements named `Family[wght]` and `Family-Italic[wght]`; ten `<instance>` elements with `stylemapfamilyname`, `stylemapstylename` and `postscriptfontname` as in the table in (c). Add name ID 25 (`Family`, `FamilyItalic`) via `openTypeNameRecords` on the two default masters.
6. **Outlines from the generator**: every closed stroke outline counter-clockwise (cubic, PostScript convention); points at horizontal and vertical extrema; integer coordinates in the masters; identical point structure across masters. Mark every glyph with more than one contour or with components `public.truetype.overlap = True` in the VF masters.
7. **Build**:
   - VF: `ufo2ft.compileVariableTTFs` / `fontmake -o variable`, overlaps kept, flags from the lib key, unhinted, with `gasp` 0xFFFF→0x000F and the 7-byte smart-dropout `prep` taken from the UFO.
   - Static TTF and static OTF in **separate** invocations, overlaps removed; add a one-value-per-axis STAT with `macNames=False`.
   - cu2qu at the default 0.001 em unless measurement of our curves says otherwise (tighten with `-e`).
   - WOFF2 as the last step, under the same `SOURCE_DATE_EPOCH`.
8. **Hinting**: VF unhinted. Static OTF: set blue zones (baseline, x-height, cap height, ascender with overshoots; descender in OtherBlues) and StemSnapH/V per master, then `otfautohint` and re-subroutinise. Static TTF: either unhinted with the same gasp/prep as the VF, or ttfautohint with `no_info`, natural stem mode for grayscale and DirectWrite, `reference_file` = Regular, then `head.flags |= 8`. Choose by looking at rendered output on Windows.
9. **Other defaults to override**: `openTypeOS2Type = []`; `openTypeOS2VendorID` (4 characters); `openTypeHeadCreated` fixed or `SOURCE_DATE_EPOCH` exported for every step; `public.openTypeCategories` for all glyphs (marks as `mark`); `languagesystem` statements in `features.fea`.
10. **Checks**: `fontbakery check-universal --skip-network` separately on static TTFs, static OTFs and the VF pair, with `-x opentype/monospace` for OTFs; plus our own assertions from decision 2, a two-build byte-comparison under different `PYTHONHASHSEED`, and a rendering test of an overlapping glyph.

### Minimal fontinfo/lib block (per master)

```python
info.unitsPerEm = 1000
info.postscriptIsFixedPitch = True
info.openTypeOS2Panose = [2, 11, 5, 9, 0, 0, 0, 0, 0, 0]
info.openTypeHheaAscender = info.openTypeOS2TypoAscender = info.openTypeOS2WinAscent = A
info.openTypeHheaDescender = info.openTypeOS2TypoDescender = -D
info.openTypeOS2WinDescent = D
info.openTypeHheaLineGap = info.openTypeOS2TypoLineGap = 0
info.openTypeOS2Selection = [7]
info.openTypeOS2Type = []
info.openTypeOS2VendorID = "XXXX"
info.openTypeOS2WeightClass = 400
info.italicAngle = 0            # negative in italic masters
info.openTypeGaspRangeRecords = [{"rangeMaxPPEM": 65535, "rangeGaspBehavior": [0, 1, 2, 3]}]
lib["public.truetype.instructions"] = {"formatVersion": "1",
    "controlValueProgram": "PUSHW[ ] 511\nSCANCTRL[ ]\nPUSHB[ ] 4\nSCANTYPE[ ]"}
lib["public.glyphOrder"] = [".notdef", *zero_width, *the_rest]
lib["public.openTypeCategories"] = {...}
glyph.lib["public.truetype.overlap"] = True   # multi-contour / composite glyphs, VF masters
```

### Open points

- Which font tables DirectWrite uses for `DWRITE_FONT_METRICS.ascent/descent/lineGap` is not documented on the page I read; decision 4 makes the answer irrelevant, but it is unverified on Windows.
- How CoreText turns hhea values into `CTFontGetAscent/Descent/Leading` (rounding, any adjustment) was not read from an Apple source.
- Nothing here was rendered on Windows or macOS; the hinting choice for static TTFs needs real screenshots.
- `fsSelection` bit 8: the spec says set it, GF tooling clears it; I found no consumer whose behaviour depends on it.
- The CFF `numberOfHMetrics = numGlyphs` statement in the recommendations is not honoured by fontTools; I found no consumer that rejects the trimmed table (OTS accepted it).
- Fontspector was not run; its results may differ from fontbakery 1.1.0.
