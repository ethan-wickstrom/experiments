# How terminals and editors turn a monospace font into a cell grid

Research report for the new monospaced family. Read 2026-11-14/15.

**Method.** Every claim below comes from a source I read myself: the application's source code on its default branch (fetched from `raw.githubusercontent.com`, `gitlab.gnome.org`, `gitlab.freedesktop.org`, `codeberg.org`), its official documentation, or a specification. Claims tagged **[measured]** are numbers I measured with fontTools 4.68 on the released font files (scripts in `scripts/`, raw output in `measure_all.json`). Claims tagged **[inference]** are my own reasoning from those sources. Source code moves: line numbers are omitted on purpose, function names are given instead.

**Not verified by rendering.** I ran no terminal and took no screenshots. Everything about behaviour is from reading code and docs.

Contents: (a) cell metrics · (b) who draws box/block/braille/Powerline · (c) stroke conventions · (d) OpenType features · (e) variable fonts, bold, italic · (f) width · (g) underline and strikethrough · (h) rasterisation and weight · What this means for our font · Gaps and disagreements.

---

## (a) How each application computes the cell

### a.1 Which font table supplies ascent, descent and line gap

The application rarely reads the tables itself. It asks a platform library, and the libraries differ:

| Library (used by) | Ascent / descent / gap come from | Source |
|---|---|---|
| FreeType `face->ascender/descender/height` (kitty on Linux, WezTerm, Alacritty on Linux, foot via fcft) | OS/2 `sTypo*` if `fsSelection` bit 7 (USE_TYPO_METRICS) is set; otherwise `hhea`; if `hhea` is all zero, `sTypo*`; if those are zero, `usWin*`. `height = ascender − descender + lineGap`. | [FreeType `sfobjs.c`, `sfnt_load_face`][ft-sfobjs] |
| HarfBuzz `hb_ot_metrics` (Pango, hence VTE) | `sTypo*` when USE_TYPO_METRICS is set and the value is non-zero, else `hhea`. | [HarfBuzz `hb-ot-metrics.cc`][hb-metrics] |
| Skia on FreeType (Chromium on Linux: xterm.js, VS Code) | `sTypo*` if USE_TYPO_METRICS, else FreeType's `face->ascender/descender`; leading = `height + descender − ascender`. | [Skia `SkFontHost_FreeType.cpp`][skia-ft] |
| Skia on CoreText (Chromium on macOS) | `CTFontGetAscent/Descent/Leading`. | [Skia `SkScalerContext_mac_ct.cpp`][skia-ct] |
| Skia on DirectWrite (Chromium on Windows) | `DWRITE_FONT_METRICS.ascent/descent/lineGap`. | [Skia `SkScalerContext_win_dw.cpp`][skia-dw] |
| Ghostty (own table parser, both back ends) | `sTypo*` if USE_TYPO_METRICS; else `hhea` if non-zero; else `sTypo*`; else `usWin*` with gap 0. | [Ghostty `freetype.zig` `getMetrics`][g-ft], [`coretext.zig`][g-ct] |
| Classic platform behaviour | "Macintosh: the ascender, descender and lineGap values in the 'hhea' table. Windows GDI: the usWinAscent and usWinDescent values in the OS/2 table." | [OpenType spec, Recommendations][ot-recom] |

Blink then rounds ascent and descent separately (`SkScalarRoundToScalar`) and sets line spacing to `lround(ascent) + lround(descent) + lround(lineGap)` ([`font_metrics.cc`][blink-fm], [`simple_font_data.cc`][blink-sfd]).

The DirectWrite documentation for [`DWRITE_FONT_METRICS`][dwrite-fm] does not say which table `ascent`/`descent` are read from (gap, see the end).

The OpenType spec's own advice for consistent line spacing: set USE_TYPO_METRICS, set `hhea.ascender = sTypoAscender`, `hhea.descender = sTypoDescender`, `hhea.lineGap = sTypoLineGap`, and either make `usWinAscent + usWinDescent` equal the typo sum, or (the "alternative guidance") make all three sets equal with both line gaps 0 ([Recommendations, "Baseline to Baseline Distances"][ot-recom]).

### a.2 Per application

| App | Cell width | Cell height | Baseline in the cell | User knobs |
|---|---|---|---|---|
| **kitty** (Linux, FreeType) | max over U+0020..U+007F of `ceil(horiAdvance)` | `ceil(face->height × scale)`; raised if the rendered `_` would fall outside | `ceil(ascender px)` from the top, so any line gap lands below the text | `modify_font cell_width 80%`, `cell_height -2px`, `baseline 3` (px, % or pt) |
| **kitty** (macOS, CoreText) | max over the same range of `ceil(CTFontGetAdvancesForGlyphs)` | `ceil` of the distance between two line origins that CoreText's typesetter produces for a test string | `floor(bounds_ascent + 0.5)` | same |
| **Ghostty** | max advance over printable ASCII, then `round()` (the code comments explain why it does not `ceil`) | `round(ascent − descent + line_gap)` | half the line gap above and half below, then the face is centred in the rounded cell: `round(half_gap − descent − (cell_h − face_h)/2)` from the bottom | `adjust-cell-width`, `adjust-cell-height` (integer px or %; text is re-centred), `adjust-font-baseline` |
| **WezTerm** | max `horiAdvance` over 32..127 from FreeType, then `ceil(width × cell_width)` | `ceil(y_scale × face->height × line_height)` | derived from `size.metrics.descender`; extra height from `line_height` is split evenly | `line_height = 1.0`, `cell_width = 1.0` (multipliers) |
| **Alacritty** | advance of `'0'` (FreeType and CoreText) or of `'!'` (DirectWrite); `floor(advance + offset.x)` | FreeType: `max(size.height, ascender − descender)`; CoreText: `round(ascent) + round(descent) + round(leading)`; DirectWrite: `ascent + descent + lineGap`; then `floor(h + offset.y)` | glyphs sit "at the bottom" of the cell by default (`glyph_offset` doc) | `font.offset = { x, y }` (integer px), `font.glyph_offset` |
| **iTerm2** | `round('W' advance × pointSize / unitsPerEm)`, then `ceil(w × horizontalSpacing)` | `ceil(NSFont.ascender − NSFont.descender + NSFont.leading)`, then `ceil(h × verticalSpacing)` | `−(floor(leading) − floor(descender + 0.5))` (0.5 is not added for Monaco) | horizontal and vertical spacing sliders; advanced setting "Use a more theoretically correct technique to measure line height" |
| **Apple Terminal** | not published | not published | not published | character and line spacing in the profile's Text tab (as used in [Textual's FAQ][textual-mac]) |
| **Windows Terminal** (AtlasEngine) | advance of `'0'` in design units × font size, `roundf` | `(ascent + descent + lineGap)` from `DWRITE_FONT_METRICS` × size, `roundf` | `round(ascent + (lineGap + cellHeight − advanceHeight)/2)` from the top (half gap above, re-centred when overridden) | `font.cellWidth`, `font.cellHeight` (CSS-like lengths; schema says the default height "is usually quite close to setting this to 1.2") |
| **VTE** (GNOME Terminal, Ptyxis, …) | max over U+0021..U+007E of `PANGO_PIXELS_CEIL(logical width)` | `PANGO_PIXELS_CEIL` of Pango's font-metrics height, used only when it is at least the measured logical height | `PANGO_PIXELS_CEIL` of Pango's metrics ascent | `cell-width-scale`, `cell-height-scale` (1.0 to 2.0) |
| **foot** | advance of rasterised `'M'` (else `max_advance`) + `letter-spacing` | `max(font.height, ascent + descent)`, each `ceil`ed by fcft; or `line-height` if set | `descent` px above the cell bottom; centred only when `line-height` is set | `line-height`, `letter-spacing`, `vertical-letter-offset` (pt or px) |
| **xterm.js** (VS Code terminal) | `measureText('W').width`, then `floor(w × devicePixelRatio)` + `round(letterSpacing)` | `fontBoundingBoxAscent + fontBoundingBoxDescent` (no line gap), `ceil(h × dpr)`, then `floor(× lineHeight)` | glyph box centred when `lineHeight ≠ 1` | `lineHeight`, `letterSpacing`; VS Code defaults `terminal.integrated.lineHeight` to 1.1 on Linux and 1 elsewhere |
| **VS Code editor** | width of `'n'` measured in the DOM | not from the font: `round(1.5 × fontSize)` on macOS, `round(1.35 × fontSize)` elsewhere, when `editor.lineHeight` is 0 | CSS line box (browser places the font's ascent+descent in the line) | `editor.lineHeight` (0 = auto, <8 = multiplier, ≥8 = px), `editor.letterSpacing` |
| **Zed terminal** | advance of `'m'`, unrounded | not from the font: `font_size × line_height`; default `"standard"` = 1.3, `"comfortable"` = 1.618 | `(line_height − ascent − descent)/2 + ascent` from the top | `terminal.line_height` (`"standard"`, `"comfortable"`, `{"custom": n}`); buffers use `buffer_line_height`, default `"comfortable"` |
| **JetBrains terminal** (JediTerm) | `FontMetrics.charWidth('W')` | `ceil(FontMetrics.getHeight() × lineSpacing)`; spacing is forced to 1.0 on the alternate screen when that setting is on | Java2D descent | line spacing setting |
| **JetBrains editor** | n/a | line height factor, default 1.2 ("120% of the point size") | n/a | Settings → Editor → Font |
| **Neovide** | advance of shaped `"M"` (swash) + `width` option, unrounded | `ceil(ascent + descent + leading + linespace)` | `ascent + (leading + linespace)/2` | `linespace`, `guifont` `:wX`, `[font] width` |

Sources: kitty [`freetype.c`][k-ft] (`calc_cell_width`, `calc_cell_height`, `cell_metrics`), [`core_text.m`][k-ct] (`cell_metrics`), [`definition.py`][k-def] (`modify_font`); Ghostty [`Metrics.zig`][g-metrics] (`calc`, `apply`), [`Config.zig`][g-config]; WezTerm [`ftwrap.rs`][w-ftwrap] (`cell_metrics`), [`harfbuzz.rs`][w-hb] (`metrics_for_idx`), [`utilsprites.rs`][w-sprites] (`RenderMetrics::new`), [`line_height.md`][w-lh], [`cell_width.md`][w-cw]; Alacritty/crossfont [`ft/mod.rs`][a-ft], [`darwin/mod.rs`][a-ct], [`directwrite/mod.rs`][a-dw], [`display/mod.rs`][a-display] (`compute_cell_size`), [`alacritty.5`][a-man]; iTerm2 [`PTYTextView.m`][i-ptv] (`charSizeForFont:`), [`FontSizeEstimator.m`][i-fse], [`PTYFontInfo.m`][i-pfi]; Windows Terminal [`AtlasEngine.api.cpp`][wt-api] (`_resolveFontMetrics`), [`profiles.schema.json`][wt-schema]; VTE [`fonts-pangocairo.cc`][v-fonts] (`measure_font`, constructor), [`vtedefines.hh`][v-defs]; foot [`terminal.c`][f-term] (`term_font_baseline` and the font-sizing code above it), [fcft `fcft.c`][f-fcft], [`foot.ini.5`][f-ini]; xterm.js [`CharSizeService.ts`][x-charsize], [`WebglRenderer.ts`][x-webgl] (`_updateDimensions`); VS Code [`terminal.ts`][vs-term] (`DEFAULT_LINE_HEIGHT`), [`fontInfo.ts`][vs-fontinfo] (`GOLDEN_LINE_HEIGHT_RATIO`), [`editorOptions.ts`][vs-opts]; Zed [`terminal_element.rs`][z-term], [`default.json`][z-default], [`line.rs`][z-line]; JediTerm [`TerminalPanel.java`][j-jedi] (`establishFontMetrics`); JetBrains [Font settings][j-font]; Neovide [`caching_shaper.rs`][n-shaper].

### a.3 Consequences worth stating

- **Rounding differs in direction.** kitty, WezTerm, VTE, foot and Neovide round the cell *up*; Ghostty and Windows Terminal round to nearest; Alacritty and xterm.js round *down*. A 0.6 em advance at 13 px is 7.8 px: the cell is 8 px in the first two groups and 7 px in the last, where each glyph is then 0.8 px wider than its cell.
- **Line gap placement differs.** Ghostty, Windows Terminal and Neovide put half the line gap above the text. kitty (Linux) and WezTerm put the baseline at the ascender, so the whole gap is below. A font with `lineGap = 0` removes this difference **[inference]**.
- **Three applications ignore the font's vertical metrics for line height**: VS Code's editor (1.35 or 1.5 × font size), Zed (1.3 or 1.618 × font size) and JetBrains' editor (1.2 × point size). In these, a box-drawing glyph only reaches the next line if its outline is tall enough.
- **VS Code decides "monospace" by measurement.** `FontMeasurements` compares the width of `n`, space, `0`–`9`, `→` (U+2192), `·` (U+00B7) and each of `|/-_ilm%` in regular, italic and bold; with ligatures on it also measures `fi`, `<=`, `=>`, `===`. If any differs from the reference width × string length by more than 0.005 px, `isMonospace` is false ([`fontMeasurements.ts`][vs-fm]).
- **kitty and GNOME need fontconfig to call the font monospace.** kitty's FAQ: a font missing from `kitten choose-fonts` "is not monospace or is a bitmapped font", and it lists fonts with `spacing=100` or `spacing=90` ([kitty FAQ][k-faq]). Fontconfig computes spacing from the advances of *encoded* glyphs, skipping zero advances, with a tolerance of 1/33: one width is MONO (100); exactly two widths in a 2:1 ratio is DUAL (90). Fontconfig's main branch adds a second stage that recovers grid fonts whose ASCII letters and digits share one advance and where at least 98 % of advances are integer multiples of the cell ([fontconfig `fcfreetype.c`, `FcSpacingClassify`][fc-spacing]). **[measured]** JetBrains Mono Bold 2.304 maps U+FEFF to a glyph with advance 351 beside 1,348 glyphs at 600; under the legacy rule that is two widths not in a 2:1 ratio.

---

## (b) Who draws box-drawing, blocks, braille, Powerline and friends

### b.1 Which code points each application draws itself

| App | Draws itself | Default | Switch |
|---|---|---|---|
| **kitty** | U+2500–259F, 25D6–25D7, 25CB, 25C9, 25CF, 25DC–25E5, 2800–28FF, E0B0–E0BF, E0D6–E0D7, EE00–EE0B (Fira Code progress bar), 1FB00–1FBAE, 1FBCE–1FBEF, 1CD00–1CDE5 (octants), 1CC1B–1CC3F, 1CE16–1CE19, 1CE51–1CEAF, F5D0–F60D (branch drawing) | always | none in `kitty.conf`; a static flag `allow_use_of_box_fonts = true` |
| **Ghostty** | U+2500–257F, 2580–259F, 2800–28FF, 25E2–25E5, 25F8–25FA, 25FF, E0B0–E0BF, E0D2, E0D4, 1FB00–1FBEF (most), 1CC1B–1CC3F, 1CD00–1CDE5, 1CE00–1CEAF (parts), F5D0–F60D | always | `font-codepoint-map = U+2500-U+259F=Family` is resolved before the sprite face |
| **WezTerm** | Box Drawing, Block Elements, Braille, sextants and smooth mosaics, Legacy Computing Supplement mosaics, Powerline triangles/curves/diagonals; in nightly also branch symbols and progress-bar symbols | `custom_block_glyphs = true` | `custom_block_glyphs = false` |
| **Alacritty** | U+2500–259F, 1FB00–1FB3B, 1FB82–1FB8B (in code), E0B0–E0B3 | `builtin_box_drawing = true` | `false` |
| **iTerm2** | 124 box-drawing characters incl. arcs and diagonals, block elements, ◢◣◤◥◸◹◺◿, sextants and smooth mosaics; Powerline E0A0–E0A2, E0B0–E0B3 and extended ones | on | advanced setting "Use your typeface's box-drawing characters instead of iTerm2's custom drawing code"; profile setting "Use built-in Powerline glyphs" |
| **Windows Terminal** | U+2500–259F (0xA0 code points), E0B0–E0BF, 1FB00–1FB94 | `font.builtinGlyphs = true` | `false` |
| **VTE** | U+23B8–23BD, 2500–259F, 25E2–25E5, 1CC1B–1CC47, 1CD00–1CDE5, 1CE09–1CE0A, 1CE16–1CE19, 1CE51–1CEAF, 1FB00–1FBAF, 1FBBD–1FBBF, 1FBCE–1FBDF, 1FBE4–1FBE7. Not braille, not Powerline. | always | none found |
| **foot** | U+2500–259F, 2800–28FF, 1CD00–1CDE5, 1FB00–1FB9B | `box-drawings-uses-font-glyphs = no` | `yes` |
| **xterm.js WebGL** (VS Code terminal) | U+2500–257F, 2580–259F, 2800–28FF, E0A0–E0D4, EE00–EE0B, F5D0–F60D, 1FB00–1FBFF | `customGlyphs: true`; VS Code `terminal.integrated.customGlyphs = true`, "only works when" GPU acceleration is on | `false`; the DOM renderer always uses the font |
| **Zed terminal** | only solid block elements as rectangles (▀ ▁–█ ▉–▏ ▐ ▔ ▕, quadrants) and ░▒▓ as flat opacity 0.25/0.5/0.75; box-drawing *lines* come from the font | always | none found |
| **Neovide** | 207 code points: U+2500–2595, E0B0–E0BF, E0D2, E0D4, E0D6–E0D7, EE00–EE05, a few 1FB7C–1FB9F, 1CC43 | `[box-drawing] mode = "native"` | `"font-glyph"` or `"selected-native"` |
| **Apple Terminal**, **JediTerm**, **VS Code editor**, **Zed editor**, **JetBrains editor** | nothing found: the font is used | | |

Sources: kitty [`fonts.c` `font_for_cell`][k-fonts]; Ghostty [`sprite/Face.zig`][g-sprite] and the `draw<CP>` function names in `sprite/draw/*.zig`, [`CodepointResolver.zig`][g-resolver]; WezTerm [`custom_block_glyphs.md`][w-cbg]; Alacritty [`builtin_font.rs`][a-builtin], [`alacritty.5`][a-man]; iTerm2 [`iTermBoxDrawingBezierCurveFactory.m`][i-box], [`iTermAdvancedSettingsModel.m`][i-adv], [Profiles → Text docs][i-doc]; Windows Terminal [`BuiltinGlyphs.h`][wt-bgh], [`profiles.schema.json`][wt-schema]; VTE [`minifont.cc`][v-minifont] (**[measured]**: I applied the regex from VTE's own [`minifont-coverage.py`][v-cov] to the `case 0x…` labels, 747 code points); foot [`foot.ini.5`][f-ini]; xterm.js [`addon-webgl.d.ts`][x-webgl-d], VS Code [`terminalConfiguration.ts`][vs-termconf]; Zed [`terminal_element.rs`][z-term] (`block_char_to_rect`, `shade_char_to_opacity`); Neovide [`box_drawing/settings.rs`][n-boxset], [`renderer.rs`][n-boxr] (**[measured]** from the `BOX_CHARS` map), [`config-file.md`][n-cfg]. For Apple Terminal the evidence is indirect: Textual's FAQ reports "misaligned blocks and lines" there and fixes them by setting line spacing to 0.805 with Menlo ([Textual FAQ][textual-mac]).

So the font's own box-drawing glyphs are what the user sees in: Apple Terminal, Zed (lines), JetBrains terminals and editors, VS Code's editor and DOM-rendered terminal, every web page and Markdown preview, and any terminal where the user switched the built-in drawing off. In kitty, Ghostty, WezTerm, Alacritty, iTerm2, Windows Terminal, VTE, foot, VS Code's GPU terminal and Neovide they are not used by default.

Why the terminals do this, in their own words: foot lists "No antialiasing effects where e.g. line endpoints appear dimmed down, or blurred", "guaranteed to span the entire cell", "No alignment issues", and missing glyphs causing badly sized fallbacks ([`foot.ini.5`][f-ini]). WezTerm's option exists "to work around a hinting issue in freetype" ([`custom_block_glyphs.md`][w-cbg]). Neovide: glyphs "might not line up correctly or might have gaps between adjacent cells … especially pronounced when using the linespace configuration option" ([`config-file.md`][n-cfg]).

### b.2 How the reference fonts dimension these glyphs **[measured]**

Files: [JetBrains Mono `fonts/ttf` on master][font-jbm], [Iosevka v33.2.5 `PkgTTF-Iosevka`][font-iosevka], [Cascadia Code v2407.24 static TTF][font-cascadia], [Fira Code 6.2][font-fira], [DejaVu 2.37][font-dejavu]. Thickness is the bounding-box width of U+2502 and height of U+2500; stems are scanline intersections of `H` at 25 % of cap height.

| Measure (Regular) | JetBrains Mono | Iosevka 33.2.5 | Cascadia Code 2407.24 | Fira Code 6.2 | DejaVu Sans Mono 2.37 |
|---|---|---|---|---|---|
| unitsPerEm | 1000 | 1000 | 2048 | 1950 | 2048 |
| advance (units / em) | 600 / 0.600 | 500 / 0.500 | 1200 / 0.586 | 1200 / 0.615 | 1233 / 0.602 |
| distinct advances of encoded glyphs | 600×1348, 0×24 | 500×5842, 1000×1388, 0×282 | 1200×2373, 0×53 | 1200×1565, 0×21 | 1233×3322 |
| hhea asc / desc / gap | 1020 / -300 / 0 | 965 / -215 / 70 | 1900 / -480 / 0 | 1800 / -600 / 0 | 1901 / -483 / 0 |
| OS/2 typo asc / desc / gap | 1020 / -300 / 0 | 965 / -285 / 0 | 1900 / -480 / 0 | 1800 / -600 / 0 | 1556 / -492 / 410 |
| OS/2 win asc / desc | 1165 / 400 | 965 / 285 | 2226 / 480 | 1800 / 600 | 1901 / 483 |
| USE_TYPO_METRICS | yes | yes | yes | yes | no |
| line height hhea / typo / win (em) | 1.320 / 1.320 / 1.565 | 1.250 / 1.250 / 1.250 | 1.162 / 1.162 / 1.321 | 1.231 / 1.231 / 1.231 | 1.164 / 1.200 / 1.164 |
| x-height / cap height (em) | 0.550 / 0.730 | 0.520 / 0.735 | 0.518 / 0.693 | 0.540 / 0.706 | n/a / n/a |
| H vertical stem (units / em) | 90 / 0.090 | 78 / 0.078 | 208 / 0.102 | 173 / 0.089 | 203 / 0.099 |
| Bold H stem (em) | 0.125 | 0.111 | 0.129 | 0.168 | 0.144 |
| post underlinePosition / Thickness (em) | -0.155 / 0.050 | -0.050 / 0.050 | -0.049 / 0.049 | -0.051 / 0.026 | -0.063 / 0.044 |
| OS/2 yStrikeoutPosition / Size (em) | 0.320 / 0.050 | 0.265 / 0.051 | 0.311 / 0.049 | 0.163 / 0.026 | 0.259 / 0.050 |
| U+2502 │ y-extent (units) | -400 … 1120 | -285 … 965 | -530 … 2226 | -1000 … 2000 | -512 … 1921 |
| │ overshoot below hhea desc / above hhea asc (units) | 100 / 100 | 70 / 0 | 50 / 326 | 400 / 200 | 29 / 20 |
| │ height (em) and ÷ hhea line height | 1.520 em; ×1.152 | 1.250 em; ×1.000 | 1.346 em; ×1.158 | 1.538 em; ×1.250 | 1.188 em; ×1.021 |
| U+2500 ─ x-overshoot each side (units; % of advance) | 20; 3.3% | 0; 0.0% | 104; 8.7% | 10; 0.8% | 20; 1.6% |
| ─ centre y vs (hhea asc+desc)/2 (units) | 370 vs 360 | 340 vs 375 | 707 vs 710 | 700 vs 600 | 704 vs 709 |
| light │ thickness (units / em / × H stem) | 100 / 0.100 / 1.11 | 70 / 0.070 / 0.90 | 208 / 0.102 / 1.00 | 160 / 0.082 / 0.92 | 160 / 0.078 / 0.79 |
| light ─ thickness (units) | 100 | 62 | 208 | 160 | 172 |
| heavy ┃ thickness (units; × light) | 200; ×2.00 | 138; ×1.97 | 416; ×2.00 | 480; ×3.00 | 320; ×2.00 |
| double ║ stroke / gap / stroke (units) | 100 / 100 / 100 | 69 / 56 / 69 | 208 / 208 / 208 | 160 / 160 / 160 | 160 / 160 / 160 |
| Bold: light │ thickness (units) | 100 | 90 | 264 | 160 | 160 |
| U+2588 █ bbox x; y (units) | 0…600; -300…1020 | 0…500; -285…965 | 0…1200; -480…2226 | 0…1200; -600…1800 | -20…1253; -512…1921 |
| U+2571 ╱ bbox x; y (units) | -20…620; -160…880 | -32…532; -297…977 | 0…1200; -518…1932 | -75…1270; -635…1837 | -89…1322; -492…1901 |
| U+2504 ┄ dash x-runs (units) | 37–163 237–363 437–563 | 33–133 200–300 367–467 | 66–333 466–733 866–1133 | 80–320 480–720 880–1120 | 60–351 471–762 882–1173 |
| U+2508 ┈ dash x-runs (units) | 25–125 175–275 325–425 475–575 | 25–100 150–225 275–350 400–475 | 37–262 337–562 637–862 937–1162 | 75–225 375–525 675–825 975–1125 | 60–248 368–556 676–864 984–1173 |
| U+254C ╌ dash x-runs (units) | 70–230 370–530 | 50–200 300–450 | 150–450 750–1050 | 80–520 680–1120 | 60–556 677–1173 |
| U+2506 ┆ dash y-runs (units) | -219–118 193–527 600–938 | -202–48 215–465 632–882 | -382–162 434–978 1250–1794 | -520–280 440–1240 1400–2200 | -403–215 395–1013 1193–1811 |
| coverage: box 2500–257F / block 2580–259F | 128 / 32 | 128 / 32 | 128 / 32 | 128 / 32 | 128 / 32 |
| coverage: braille / Powerline E0A0–E0D7 / legacy 1FB00–1FBFF / branch F5D0–F60D | 0 / 7 / 0 / 0 | 256 / 22 / 247 / 0 | 256 / 0 / 168 / 0 | 0 / 7 / 0 / 0 | 0 / 0 / 0 / 0 |

Rounded corner U+256D, centreline radius where the straight stub ends (approximate, 1-unit deviation threshold): JetBrains Mono ≈ 255 units (0.42 × advance), Iosevka ≈ 204 (0.41), Cascadia ≈ 559 (0.47), Fira Code ≈ 424 (0.35), DejaVu ≈ 230–299 (0.19–0.24).

What the table shows:

1. **Horizontal centre is exact everywhere** (x-centre of │ = advance/2, except DejaVu's 616.0 vs 616.5).
2. **Vertical strategy splits three ways.** Iosevka spans exactly its typo/win box (1.25 em), no overshoot at all. JetBrains Mono overshoots symmetrically by 0.10 em each side to 1.52 em. Fira Code spans 1.538 em asymmetrically, and its horizontal line sits 100 units above the cell centre. Cascadia runs from 50 units below the descender up to `usWinAscent`.
3. **Block elements are kept to the cell** in JetBrains Mono, Iosevka and Fira Code (█ is exactly advance × hhea box). Cascadia's █ extends 326 units above the hhea ascender; DejaVu's overshoots by 20–29 units on every side.
4. **Thickness is roughly the regular stem** (0.79–1.11 ×). Three of five keep it constant in Bold; Cascadia tracks the bold stem exactly; Iosevka grows 70 → 90.
5. **Dashes tile**: in JetBrains Mono, Iosevka, Cascadia and Fira Code the margin at each cell edge is half the gap, so the rhythm continues across cells (e.g. JetBrains Mono ┈: margin 25, dash 100, gap 50).

### b.3 What a font glyph must do to connect, and what breaks **[inference from a.2 and b.1]**

- **Across cells horizontally.** With ceil-rounded cells the cell can be up to 1 px wider than the glyph's advance. A horizontal stroke ending exactly at 0 and at the advance leaves a hairline. An overshoot of *o* em per side closes a gap of 2·*o*·ppem pixels: JetBrains Mono's 0.02 em closes 0.52 px at 13 px/em; Cascadia's 0.051 em closes 1.3 px.
- **Across lines vertically.** Where line height comes from the font's metrics and no extra spacing is set, a stroke from descender to ascender (plus line gap) meets the next line. Where the application sets line height as a multiple of the font size and centres the font's ascent+descent box in it (Zed, CSS line boxes), the stroke must span at least that multiple of the em, centred on the middle of the ascent+descent box: 1.2 em (JetBrains default), 1.3 em (Zed terminal), 1.35 em (VS Code editor on Windows/Linux), 1.5 em (VS Code editor on macOS), 1.618 em (Zed buffer). Measured spans: Iosevka 1.25, Cascadia 1.35, JetBrains Mono 1.52, Fira Code 1.54.
- **When the user raises line height** in an application that uses font glyphs (Apple Terminal line spacing, JediTerm line spacing, `terminal.integrated.lineHeight` with the DOM renderer, Zed `"comfortable"`), vertical lines gap as soon as the line height exceeds the glyph's span. Zed's own default comment says `"standard"` (1.3) "is useful for TUIs, particularly if they use box characters" ([`default.json`][z-default]). JediTerm has a setting that forces spacing 1.0 on the alternate screen ([`TerminalPanel.java`][j-jedi]).
- **When the user lowers line height** (Textual recommends 0.805 for Menlo in Apple Terminal), strokes overlap, which is invisible for solid lines but breaks dashed verticals and makes ▀/▄ unequal.
- **When the user changes letter spacing or cell width**, horizontal lines gap by the added amount; no reference font overshoots enough to cover even +1 px at small sizes. WezTerm says of `cell_width`: glyphs "won't be stretched but will render further apart" ([`cell_width.md`][w-cw]).
- **Terminals that draw the glyphs themselves are immune**: xterm.js says its custom glyphs give "continuous lines, even when line height and letter spacing is used" ([`addon-webgl.d.ts`][x-webgl-d]); Ghostty adjusts "Powerline glyphs … along with the cell height" ([`Config.zig`][g-config]).
- **Oversized ink can trigger rescaling.** kitty's FreeType path re-renders a glyph at a smaller size when its bitmap is wider than its cells by more than 1 px (an excess of exactly 2 px on a single cell is cropped instead; italic glyphs with an excess under half a cell are trimmed) ([`freetype.c` `render_bitmap`][k-ft]). WezTerm scales a glyph down when it is wider than `cell_width × (cells + 0.25)` unless overflow is allowed ([`glyphcache.rs`][w-gc]). kitty never asks the font for box drawing, so this limits the overshoot of *text* glyphs, not of box glyphs there.

---

## (c) Stroke conventions

### c.1 What the self-drawing terminals use for light and heavy

| App | Light line | Heavy line | Notes |
|---|---|---|---|
| kitty | `box_drawing_scale` level 1 = 1 pt × dpi/72, `ceil` | level 3 = 2 pt | default `0.001, 1, 1.5, 2` pt for thin, normal, thick, very thick; scales with zoom |
| Ghostty | `box_thickness` = the font's underline thickness in px (`ceil`, min 1) | 2 × | `adjust-box-thickness`; "super light" = max(base/2, 1) |
| WezTerm | underline thickness (rounded, min 1 px) | stroke width × 3.01 in code (the enum comment says "twice") | `OutlineThin` is a fixed 1.2 px |
| Alacritty | `round(cell_width / 8)`, min 1 px | 2 × | changelog: "Builtin font thickness is now based on cell width instead of underline thickness" |
| Windows Terminal | `max(1, round(cell_width / 6))` | 2 × | comment: "1/6th of the cell width roughly matches the thin line width that Cascadia Mono uses"; corner radius `min(5 × light, min(w, h)/2)` |
| VTE | `max(font_width / 5, 1)` (integer division) | light + 2 px; 3 × light for the double-line range U+2550–256C | |
| foot | `max(1, 0.04 pt × scale × cell diagonal px × dpi/72)` | 3 × | `tweak.box-drawing-base-thickness = 0.04` |
| iTerm2 | 1 pt (`lineWidth = scale`) | built from the same strokes | |
| Neovide | 2 px | 4 px | `[box-drawing.sizes] default = [2, 4]`, per-size overrides |

Sources: [kitty `definition.py`][k-def], [`decorations.c`][k-dec] (`thickness_as_float`; `C(L'─', hline, 1)`, `C(L'━', hline, 3)`); [Ghostty `Metrics.zig`][g-metrics], [`sprite/draw/common.zig`][g-common]; [WezTerm `customglyph.rs`][w-cg] (`PolyStyle::apply`), [`utilsprites.rs`][w-sprites]; [Alacritty `builtin_font.rs`][a-builtin] (`calculate_stroke_size`), [CHANGELOG][a-changelog]; [Windows Terminal `BuiltinGlyphs.cpp`][wt-bg] (`DrawBuiltinGlyph`); [VTE `minifont.cc`][v-minifont]; [foot `box-drawing.c`][f-box], [`foot.ini.5`][f-ini]; [iTerm2 `iTermBoxDrawingBezierCurveFactory.m`][i-box]; [Neovide `settings.rs`][n-boxset].

For a 0.6 em advance these give a light line of 0.075 em (Alacritty), 0.10 em (Windows Terminal), 0.12 em (VTE), and 1/12 em = 0.083 em in kitty at a 12 pt font size **[arithmetic]**. Ghostty and WezTerm take it from **our** `post.underlineThickness`.

### c.2 Arcs, dashes, diagonals

- **Arcs (U+256D–2570).** Reference radii are 0.35–0.47 of the advance in four fonts and about 0.2 in DejaVu **[measured]**. Windows Terminal uses `min(5 × light, half the smaller cell side)`. kitty's changelog records a fix giving rounded corners "a uniform line width" ([changelog][k-changelog]).
- **Dashes.** Four of five reference fonts place half a gap at each cell edge so that the pattern tiles **[measured]**.
- **Diagonals (U+2571–2573).** Ghostty prepares the sprite canvas "with an extra quarter of the width/height on each edge" precisely so that "box-drawing diagonals" can be drawn "with enough overlap so that they can seamlessly connect across corners of cells" ([`sprite/draw/README.md`][g-drawreadme]). Alacritty enlarges the canvas for the same three characters "since for proper contiguous lines they require drawing on neighbour cells" ([`builtin_font.rs`][a-builtin]). kitty's changelog records a fix for diagonal thickness "not the same as horizontal/vertical lines". **[measured]** Iosevka, Fira Code and DejaVu run the diagonal through the corners of the cell box and let the stroke overshoot (e.g. Iosevka −32…532 × −297…977 for a 500 × 1250 box); JetBrains Mono does not (its diagonal spans only −160…880 vertically).

---

## (d) OpenType features and ligatures

| App | Shaping across cells | Default | Turn features on/off | Cursor behaviour |
|---|---|---|---|---|
| kitty | HarfBuzz; ligature groups rendered into N cells | on | `font_features FiraCode-Retina +zero +onum` (keyed by **PostScript name**), or in the font spec: `font_family family="Fira Code" features="+zero cv01=2"`; `disable_ligatures never\|cursor\|always` | `disable_ligatures cursor` shows the separate glyphs under the cursor |
| Ghostty | HarfBuzz (CoreText shaper on macOS) | on | `font-feature = -calt`, `font-feature = ss01`, comma lists, CSS-compatible syntax; "To generally disable most ligatures, use `-calt, -liga, -dlig`" | `font-shaping-break = cursor` (default since 1.2.0) breaks the run under the cursor |
| WezTerm | HarfBuzz | on | `config.harfbuzz_features = { 'calt=0', 'clig=0', 'liga=0' }`; per font: `wezterm.font { family = '…', harfbuzz_features = { 'zero' } }` | none documented |
| Alacritty | none: glyphs are rasterised per character (`GlyphKey.character`), and `[font]` has no feature option | n/a | n/a | n/a |
| iTerm2 | CoreText, only with the profile's ligature setting | off | Profiles → Text → ligatures: "it disables the GPU renderer … it uses a slower API"; advanced: "Enable contextual alternates (calt)" default yes; "disallowing alphanumeric characters to belong to ligatures" default yes | none documented |
| Windows Terminal | DirectWrite; `liga`, `clig`, `calt` set to 1 whenever the user gives any feature | on | `"font": { "features": { "ss01": 1, "liga": 0 } }` | none documented |
| VTE | none: glyph cache is built per character; the sample string is spaced "to make sure ligatures aren't used when caching the glyphs: bug 793391" | n/a | not found | n/a |
| foot | grapheme clusters only (`grapheme-shaping`), so no multi-cell ligatures **[inference]** | n/a | fontconfig syntax: `font=Iosevka:fontfeatures=cv01=1:fontfeatures=cv06=1` | n/a |
| xterm.js / VS Code terminal | `addon-ligatures` reads GSUB from the font file and tells the renderer which cells to draw together | off | `terminal.integrated.fontLigatures.enabled` (false), `.featureSettings` (default `"calt" on`, CSS syntax), `.fallbackLigatures` (a fixed list used when the font cannot be parsed) | not documented |
| VS Code editor | browser (HarfBuzz in Chromium) | off | `editor.fontLigatures: true` = `"liga" on, "calt" on`; or a CSS string such as `"'ss01', 'zero'"` | none |
| Zed | platform shaper | on | `"buffer_font_features": { "calt": false, "cv01": 7 }`; `terminal.font_features` | none documented |
| JetBrains | Java2D | off | "Enable ligatures"; "Character variants: Configures OpenType stylistic sets" | none documented |
| Neovide | swash | on | `[font.features] "Family" = ["+ss01", "-calt", "ss02=2"]` | none documented |

Sources: [kitty `definition.py`][k-def], [`choose-fonts.rst`][k-choose]; [Ghostty `Config.zig`][g-config]; [WezTerm `font-shaping.md`][w-shaping]; [crossfont `ft/mod.rs`][a-ft], [`alacritty.5`][a-man]; [iTerm2 Profiles → Text][i-doc], [`iTermAdvancedSettingsModel.m`][i-adv]; [Windows Terminal `AtlasEngine.api.cpp` `_updateFont`][wt-api], [profile docs][wt-docs]; [VTE `fonts-pangocairo.cc`][v-fonts]; [`foot.ini.5`][f-ini]; [xterm.js `addon-ligatures/README.md`][x-lig], [VS Code `terminalConfiguration.ts`][vs-termconf], [`editorOptions.ts`][vs-opts]; [Zed `default.json`][z-default], [settings reference][z-docs]; [JetBrains Font settings][j-font]; [Neovide `config-file.md`][n-cfg].

**How kitty decides which glyphs form one multi-cell ligature** ([`fonts.c`][k-fonts], the comment above `group_normal` and the functions `is_special_glyph`, `is_empty_glyph`, `detect_spacer_strategy`, `ligature_type_from_glyph_name`):

1. A glyph is *special* if it is not the glyph the cmap gives for that cell's code point.
2. A glyph is *empty* if its outline has zero width.
3. kitty shapes `===` (and `###`) once per font to learn whether empty spacer glyphs come *before* the visible glyph (Fira Code: `EMPTY, EMPTY, WIDE`) or *after* it (Cascadia Code: `WIDE, EMPTY, EMPTY`). It also probes `==`, `->`, `<-`, `<<=`, `<==>` for Iosevka's glyph-name suffixes `.join-l`, `.join-m`, `.join-r`.
4. Arbitrary-length arrows are recognised by glyph names ending `_start.seq`, `_middle.seq`, `_end.seq`.
5. A single wide glyph replacing N characters (the comment's example: Operator Mono Lig) is rendered as "one glyph in N cells".

A ligature longer than 9 cells whose glyph count equals its cell count is treated as an "infinite ligature" with repeated sprites.

---

## (e) Variable fonts, bold and italic

| App | Set an axis value or instance | How bold / italic are found | Synthetic styles |
|---|---|---|---|
| kitty | any 4-letter key in the font spec is an axis: `font_family family=SourceCodeVF variable_name=SourceCodeUpright wght=380`; `style="…"` picks a named instance; `kitten choose-fonts` has sliders | `bold_font auto` etc.: for a variable family kitty picks the best file with the OS matcher, then sets each axis from the **STAT** table's axis values (format 1 or 2) by name: for `wght` the names `semibold, bold, heavy, black` when bold, `regular, medium` otherwise; for `ital`/`slnt` the names `italic, oblique, slanted, slant`. The regular face is the fvar named instance called `Regular`, else STAT values named `Regular` | not examined |
| Ghostty | `font-variation = wght=450`, plus `font-variation-bold`, `-italic`, `-bold-italic`; `font-style = Heavy` picks a named style; "if a font only supports weights from 100 to 700, setting `wght=800` will do nothing (it will not be clamped)" | searches the regular family for the style | `font-synthetic-style`: on by default; bold "by drawing an outline around the glyph", italic "by applying a slant" |
| WezTerm | named instances only: `wezterm.font('Cascadia Code', { weight = 'DemiLight' })`; `wezterm ls-fonts --list-system` prints each instance as `variation=N` (it calls `FT_Set_Named_Instance`) | attribute matching (`weight`, `stretch`, `italic`), `font_rules` | "able to synthesize basic bold and italics (really, oblique)" |
| Alacritty | `{ family = "…", style = "…" }` only; no axis key | style names `Bold`, `Italic`, `Bold Italic` | not examined |
| iTerm2 | not verified | repeated `NSFontManager convertWeight:YES` until the weight is ≥ regular + 4 (scale 0–9, advanced setting) with the same traits; italic via `convertFont:toHaveTrait:NSItalicFontMask` | if no bolder face is found "the regular font will be double-struck with a small offset" |
| Windows Terminal | `"font": { "axes": { "wght": 350 } }`, `"weight": "semi-light"` or 100–990 | bold cells use `wght = 700` (`DWRITE_FONT_WEIGHT_BOLD`); italic cells set `ital = 1` **and** `slnt = −12` when the user has given any axis, else ask DirectWrite for `DWRITE_FONT_STYLE_ITALIC`. But `intenseTextStyle` defaults to `"bright"`: SGR 1 is drawn brighter, not bolder, unless set to `"bold"` or `"all"` | DirectWrite's |
| VTE | Pango font description | bold = regular weight + 300 (capped at 1000); italic = `PANGO_STYLE_ITALIC` | Pango/fontconfig's |
| foot | fontconfig pattern (`:weight=bold:slant=italic`); axis syntax not verified | `font-bold`, `font-italic`, `font-bold-italic`, else the regular pattern's bold/italic variants | fcft honours fontconfig's `embolden` |
| xterm.js / VS Code terminal | `terminal.integrated.fontWeight` and `fontWeightBold`: `"normal"`, `"bold"` or 1–1000 (passed to the canvas `font` string); no variation setting | CSS font matching in Chromium; `drawBoldTextInBrightColors` default true | browser's |
| VS Code editor | `editor.fontVariations: true` translates `editor.fontWeight` to `font-variation-settings`; or an explicit string such as `"'wght' 450"` | CSS | browser's |
| Zed | `buffer_font_weight` 100–900; no axis setting in the settings reference | platform matcher | not examined |
| JetBrains | "Typography Settings: Main weight, Bold weight" | chosen weights | JediTerm uses `Font.deriveFont(Font.BOLD / ITALIC)` |
| Neovide | style string `W<weight>` for a variable weight (`style = "W400"`), or names `Thin … ExtraBlack`, `Italic`, `Oblique` | `[font.bold]`, `[font.italic]` tables; "if … not found, it will fallback to normal font with this weight" | not examined |

Sources: [kitty `choose-fonts.rst`][k-choose], [`fonts/common.py`][k-common] (`find_medium_variant`, `get_design_value_for`, `find_bold_italic_variant`); [Ghostty `Config.zig`][g-config]; [WezTerm `ftwrap.rs` `variations`][w-ftwrap], [`fonts.md`][w-fonts], [`wezterm.font`][w-font]; [`alacritty.5`][a-man]; [iTerm2 `PTYFontInfo.m`][i-pfi], [`iTermAdvancedSettingsModel.m`][i-adv]; [Windows Terminal `AtlasEngine.cpp` `_recreateFontDependentResources`, `_mapCharacters`][wt-engine], [`profiles.schema.json`][wt-schema]; [VTE `drawing-context.cc`][v-draw], [`vtedefines.hh`][v-defs]; [`foot.ini.5`][f-ini], [fcft][f-fcft]; [VS Code `terminalConfiguration.ts`][vs-termconf], [`editorOptions.ts`][vs-opts], [xterm.js `TextureAtlas.ts`][x-atlas]; [Zed `default.json`][z-default]; [JetBrains Font settings][j-font], [JediTerm][j-jedi]; [Neovide `config-file.md`][n-cfg].

**[measured]** How the reference variable fonts are labelled: JetBrains Mono `[wght]` 100–800 (default 400) with named instances Thin … ExtraBold and STAT values in format 1 except Regular (format 3, linked); Cascadia Code `wght` 200–700 with ExtraLight, Light, SemiLight (350), Regular, SemiBold, Bold; Fira Code `wght` 300–700 with Light, Regular, Medium, SemiBold, Bold and STAT format 2 ranges. All three have a named instance called `Regular`. kitty's key order for bold is `('semibold', 'bold', 'heavy', 'black')` and it takes the lowest index, so with these labels kitty's automatic bold may resolve to SemiBold (600) rather than Bold (700) unless other family data overrides it **[inference from `get_design_value_for`; not tested]**.

The OpenType spec adds: variable fonts "should include" `postScriptNameID` in every fvar instance record, and name IDs 16 and 17 are required ([Recommendations][ot-recom]).

---

## (f) Width: wide glyphs, ambiguous width, emoji, symbols

### f.1 The rules

- **Unicode.** "Ambiguous characters … If the context cannot be established reliably, they should be treated as narrow characters by default." "Private-use characters are considered ambiguous by default" ([UAX #11, revision 46][uax11]).
- **kitty's published width algorithm**: width 2 for regional indicators, for `EastAsianWidth` W and F, for `Basic_Emoji` not listed with FE0F, and so on; width 0 for marks (categories M*, Cf); "All remaining code points have a width of one cell". U+FE0E and U+FE0F can change the previous character's width ([text-sizing protocol][k-sizing]).
- **kitty's symbol-scaling rule** ([`fonts.c`, the `render_line` loop][k-fonts], [`narrow_symbols`][k-def]): when a cell's character is (i) a symbol found in a fallback font rather than the main font, or (ii) private-use and not drawn by kitty, or (iii) a non-emoji dingbat in U+2700–27BF or U+1F100–1F1FF, kitty computes `desired_cells = ceil(glyph width / cell width)` and lets the glyph grow over up to 4 following cells that contain a space or en-space, centring it. `narrow_symbols` caps this per range.
- **Ghostty's constraint logic** ([`renderer/cell.zig` `constraintWidth`, `isSymbol`][g-cell], [`generic.zig` `addGlyph`][g-generic]): a "symbol-like" code point (anything in a private use area, plus Arrows, Dingbats, Emoticons, Miscellaneous Symbols, Enclosed Alphanumerics and Supplement, Miscellaneous Symbols and Pictographs, Transport and Map) may be drawn up to 2 cells wide if the next cell is empty or a space, the previous cell is not also a symbol, and it is not in the last column. Symbols without a Nerd Font rule are scaled to *fit* their constraint; non-symbols get no constraint at all. Nerd Font code points use a generated per-glyph table.
- **WezTerm**: `allow_square_glyphs_to_overflow_width = "WhenFollowedBySpace"` (default) for glyphs with aspect ratio ≥ 0.7 in code (the doc says "larger than 0.9"); `treat_east_asian_ambiguous_width_as_wide = false` by default ([docs][w-square], [docs][w-ambig], [`glyphcache.rs`][w-gc]).
- **xterm.js**: `rescaleOverlappingGlyphs` shrinks single-cell glyphs "that would overlap following cell(s) … typically … ambiguous width characters (eg. the roman numeral characters U+2160+)"; never for emoji, Powerline or Nerd Font glyphs; VS Code enables it by default ([`xterm.d.ts`][x-typings], [`terminalConfiguration.ts`][vs-termconf]).
- **iTerm2**: profile option "Ambiguous characters are double-width"; advanced "Draw certain Powerline symbols double-width" (default yes, "An example code point that is affected is U+E0B8") ([docs][i-doc], [`iTermAdvancedSettingsModel.m`][i-adv]).
- **foot**: `grapheme-width-method = double-width` by default ([`foot.ini.5`][f-ini]). **Ghostty**: `grapheme-width-method = unicode` ([`Config.zig`][g-config]).

### f.2 Which symbols are safe in one cell **[measured]**

I classified code points with [`EastAsianWidth.txt`][eaw] (Unicode 18.0.0) and [`emoji-data.txt`][emoji-data].

| Class | Width in a default terminal | Examples |
|---|---|---|
| EAW N or Na, not Emoji | 1, everywhere | `✓` U+2713, `✗` U+2717, `✘`, `✕`, `❯` U+276F, `❮`, `➜` U+279C, `➤`, `▸▹▾▿◂◃` (small triangles), `►◄`, `◉ ◌ ◦`, `☐ ☒`, `⌘ ⌥ ⌃ ⏎ ⌫ ⌦ ⎋`, `⏵ ⏴ ⏶ ⏷`, `⏻ ⏼ ⏽`, `⚑ ⚐`, `⋮ ⋯ ⋅ ∘ ∙ ∅ ∉ − ∓ ≃ ≅ ⊗ ⊢ ⊣ ⊤`, `⟵ ⟶ ⟹ ⟦ ⟧ ⟨ ⟩`, `ℕ ℤ ℚ ℝ ℂ ℵ`, `▐ ░`, all 256 braille patterns, all of Supplemental Arrows-A/B, Misc Math A/B, Supplemental Math Operators, Math Alphanumerics, Legacy Computing |
| EAW A (ambiguous), not Emoji | 1 by default; 2 if the user turns on an "ambiguous is wide" option | **112 of 128 box-drawing characters and 20 of 32 block elements**, `← ↑ → ↓ ⇒ ⇔`, `• · … – — ′ ″ ° ± × ÷ § ¶`, `∀ ∂ ∃ ∇ ∈ ∋ ∏ ∑ √ ∝ ∞ ∠ ∧ ∨ ∩ ∪ ∫ ≈ ≠ ≡ ≤ ≥ ≪ ≫ ⊂ ⊃ ⊆ ⊇ ⊕ ⊥`, `■ □ ▲ △ ▼ ▽ ◆ ◇ ○ ● ◎ ◐ ◑ ★ ☆`, Greek letters, `① ②`, all private-use code points (Powerline, branch drawing) |
| Emoji = Yes, Emoji_Presentation = No | 1 by the tables, but a fallback to a colour emoji font or a following U+FE0F can make it 2 or make it overflow | `↔ ↕ ↩ ↪ ▶ ◀ ▪ ▫ ◻ ◼ ☑ ✔ ✖ ✳ ✴ ➡ ⬅ ⬆ ⬇ ⚠ ⚙ ☀ ☁ ⏸ ⏹ ⏺ ⏱ ♠ ♣ ♥ ♦ © ® ™` |
| EAW W, or Emoji_Presentation = Yes | 2 | `⏩ ⏪ ⏳ ⌚ ⌛ ◽ ◾ ❌ ❓ ❗ ⬛ ⬜ ⭐ ⭕ ⚡ ☕`, and `☰` U+2630 (W in Unicode 18.0.0's file) |

Block counts (EAW class, emoji flag): Arrows U+2190–21FF: 95 N, 15 A, 8 with Emoji=Yes. Mathematical Operators: 206 N, 50 A. Geometric Shapes: 60 N, 28 A, 6 Emoji, 2 wide. Miscellaneous Technical: 235 N, 10 wide. Dingbats: 148 N, 18 Emoji text-default, 15 wide, 11 A.

---

## (g) Underline and strikethrough

The spec: `post.underlinePosition` is the "Suggested y-coordinate of the top of the underline" (the PostScript centre definition "is not used in the 'post' table"); `underlineThickness` "should match the thickness of the underscore character (U+005F LOW LINE), and should also match the strikeout thickness" ([post table][ot-post]). FreeType converts to the centre: `underline_position = post.underlinePosition − underlineThickness/2` ([`sfobjs.c`][ft-sfobjs]).

| App | Underline position / thickness | Strikethrough position / thickness |
|---|---|---|
| kitty (Linux) | FreeType's values; thickness `ceil`, min 1 px | OS/2 `yStrikeoutPosition`/`yStrikeoutSize` if non-zero, else `floor(0.65 × baseline)` and underline thickness |
| kitty (macOS) | CoreText's underline position and thickness | always `floor(0.65 × baseline)`; thickness = underline thickness |
| Ghostty | `post` values read as the **top** of the stroke; thickness `ceil`, min 1; if thickness is 0 the table is treated as broken and it falls back to 15 % of the x-height, one thickness below the baseline | OS/2 values; if `yStrikeoutSize` is 0, centred at half the x-height with underline thickness |
| WezTerm | FreeType's values; thickness `round`, min 1 | **derived**: `(cell_height + descender − underline_position) / 2`; OS/2 not read |
| Alacritty | FreeType / CoreText / DirectWrite values (fallback for bitmap fonts) | OS/2 via FreeType and DirectWrite; on macOS "CoreText doesn't provide strikeout so we provide our own": `line_height/2 − descent` |
| iTerm2 | computed with `NSLayoutManager` for the font | not examined |
| Windows Terminal | `DWRITE_FONT_METRICS.underlinePosition/Thickness`, `round`, min 1; double underline lines are half as thick | `DWRITE_FONT_METRICS.strikethroughPosition/Thickness` |
| VTE | **not from the font**: thickness `max(min(descent/2, height/14), 1)`, position ascent + thickness (a FIXME says to use Pango's metrics) | **not from the font**: `ascent − height/4` |
| foot (fcft) | FreeType's values, `trunc(position + thickness/2)`, thickness `round`, min 1; estimated if position is 0 | OS/2 values; if position is 0, "xterm's algorithm" `3·ascent/8 − thickness/2` |
| Zed | from line height, ascent and descent (`underline_y_offset`) | derived from ascent and baseline offset; OS/2 not read |
| Neovide | swash `underline_offset`, else `−stroke_size`; `[font] underline_offset` | not examined |
| Chromium (xterm.js DOM, VS Code editor) | Skia's underline position and thickness when the font has them | not examined |

Sources: [kitty `freetype.c`][k-ft], [`core_text.m`][k-ct]; [Ghostty `freetype.zig`][g-ft], [`Metrics.zig`][g-metrics]; [WezTerm `harfbuzz.rs`][w-hb], [`utilsprites.rs`][w-sprites], [`strikethrough_position.md`][w-strike]; [crossfont][a-ft], [darwin][a-ct], [directwrite][a-dw]; [iTerm2 `PTYFontInfo.m`][i-pfi]; [Windows Terminal `AtlasEngine.api.cpp`][wt-api]; [VTE `vte.cc` `apply_font_metrics`][v-vte]; [fcft][f-fcft]; [Zed `line.rs`][z-line]; [Neovide `caching_shaper.rs`][n-shaper]; [Blink `simple_font_data.cc`][blink-sfd].

Adjusting: kitty `modify_font underline_position -2`, `underline_thickness 150%`, `strikethrough_position 2px`; Ghostty `adjust-underline-position`, `adjust-underline-thickness`, `adjust-strikethrough-*`; WezTerm `underline_position`, `underline_thickness`, `strikethrough_position`; foot `underline-offset`, `underline-thickness`, `strikeout-thickness`.

---

## (h) Rasterisation, gamma and apparent weight

- **FreeType's own account.** "Text must be rendered with linear alpha blending and gamma correction"; "No toolkit in the Linux ecosystem does it by default"; "Windows and Mac OS X do it natively" ([FreeType, "On slight hinting, proper text rendering, stem darkening and LCD filters"][ft-text]). Gamma correction makes glyphs "thin out"; "Mac OS X and Adobe's proprietary font rendering library implement a counter-measure: stem darkening at smaller sizes" ([`ftdriver.h`, `no-stem-darkening`][ft-driver]).
- **Stem darkening is off by default in FreeType**: the CFF driver initialises `no_stem_darkening = TRUE` ([`cffobjs.c`][ft-cff]) and so does the autofitter ([`afmodule.c`][ft-af]). When enabled, the default curve adds 0.4 px to stems of 0.5 px or less, 0.275 px between 1 and 1.667 px, and nothing from 2.333 px ([FreeType properties reference][ft-props]). It can be enabled with `FREETYPE_PROPERTIES="cff:no-stem-darkening=0"`; foot's manual says it is "only available for CFF fonts (OpenType, .otf)" there ([`foot.ini.5`][f-ini]).
- **TrueType hinting in FreeType** defaults to interpreter version 40 when subpixel hinting is compiled in, "roughly equivalent to the hinting provided by DirectWrite ClearType" ([`ftdriver.h`][ft-driver], [`ttobjs.c`][ft-tt]). Ghostty's default FreeType flags are `hinting`, `autohint` and `light` ([`Config.zig`][g-config]); WezTerm's default `freetype_load_target` is `"Normal"` ([docs][w-ftload]); kitty maps fontconfig's hintstyle ≥ 3 to `FT_LOAD_TARGET_NORMAL` and 1–2 to `LIGHT` ([`freetype.c`][k-ft]).
- **kitty** `text_composition_strategy platform`: gamma 1.7 and 30 % extra contrast on macOS, gamma 1.0 and 0 % on Linux; `legacy` "will make dark text on light backgrounds look thicker and light text on dark backgrounds thinner". `macos_thicken_font` is called obsolete ([`definition.py`][k-def]).
- **Ghostty** `alpha-blending`: `native` on macOS, `linear-corrected` elsewhere; plain `linear` "makes dark text look much thinner than normal and light text much thicker". `font-thicken` (macOS only, off by default) with `font-thicken-strength` 0–255 ([`Config.zig`][g-config]).
- **foot** `gamma-correct-blending = no` by default; when on, "bright glyphs on a dark background will appear thicker, and dark glyphs on a light background will appear thinner", and "many fonts have been developed on systems that do not do gamma-correct blending, and may therefore look thicker than intended" ([`foot.ini.5`][f-ini]).
- **macOS.** Alacritty "reads `AppleFontSmoothing` from user defaults to control font smoothing"; thin strokes are obtained with `defaults write -g AppleFontSmoothing -int 0` ([CHANGELOG][a-changelog]). iTerm2: "Anti-aliased text will be drawn with thinner strokes by default on Retina displays when the background color is darker" ([docs][i-doc]).
- **Windows.** Windows Terminal reads gamma and enhanced contrast from DirectWrite's rendering parameters (`DWrite_GetRenderParams`, separate values for ClearType and grayscale) and applies them in its shader ([`BackendD3D.cpp`][wt-d3d]); `antialiasingMode` defaults to `"grayscale"` ([`profiles.schema.json`][wt-schema]).

**What this means for weight [inference].** The same outline is heaviest on macOS with font smoothing on, lighter in kitty or Ghostty on Linux, and lightest for dark text with linear blending or with macOS thin strokes. The reference fonts' regular stems are 0.078–0.102 em **[measured]**. A user who wants the same optical weight everywhere needs steps finer than Regular/Bold, and half the applications in section (e) can only choose named instances or static files.

---

## What this means for our font

Values are in units of a 1000-unit em unless stated. Items marked **[inference]** are my recommendation from the evidence above, not something a source prescribes.

### 1. Make every engine compute the same cell

- Set `hhea.ascender = OS/2.sTypoAscender = usWinAscent` and `hhea.descender = sTypoDescender = −usWinDescent`, both line gaps 0, and set `fsSelection` bit 7. This is the OpenType spec's "alternative guidance", and it makes FreeType, HarfBuzz, Skia, Ghostty and the classic Mac and GDI rules agree (a.1). It also removes the half-gap-above versus gap-below difference (a.3). Fira Code already does exactly this.
- Keep ascender − descender in the 1.20–1.32 em band of the references. A height that is an integer number of pixels at common sizes matters less than it seems, because every terminal rounds differently (a.3).
- Put no ink of any *text* glyph outside [descender, ascender]: kitty raises the cell for a low underscore, Ghostty tells users to "nag the font author".
- `numberOfHMetrics`: the spec suggests 3 for monospaced fonts (TrueType outlines only).

### 2. Be monospace by every test

- One advance for every glyph that is in the cmap; zero only for combining marks. No 2-cell glyphs in the main font (Iosevka's 1,388 wide glyphs make it dual-width). Give U+FEFF and all other format characters either 0 or the cell advance: JetBrains Mono Bold's 351-unit U+FEFF is the cautionary case.
- Same advance in every weight and in italic, and for `→` (U+2192) and `·` (U+00B7): VS Code tests exactly these, to 0.005 px.
- Every ligature must keep total advance = N × cell: VS Code measures `fi`, `<=`, `=>`, `===`.
- Set `post.isFixedPitch = 1`, PANOSE proportion 9, `OS/2.xAvgCharWidth` = the advance (all five references that are single-width do the first; table b.2 for the advance).
- Add a build check that runs fontconfig's rule (cmap glyphs, non-zero advances, 1/33 tolerance) and VS Code's list.

### 3. Box drawing, blocks and Powerline in the font

These glyphs are what users see in Apple Terminal, Zed, JetBrains, VS Code's editor, the web, and anywhere built-in drawing is switched off (b.1).

| Item | Recommended value | Basis |
|---|---|---|
| x-centre of vertical strokes | exactly advance/2 | all references |
| y-centre of horizontal strokes | exactly (ascender + descender)/2 | self-drawing terminals centre in the cell; Iosevka and Cascadia (±3) do; avoids Fira Code's +100 offset |
| Horizontal overshoot of lines | 0.03 em each side (5 % of a 0.6 em advance) | closes ceil-rounding gaps up to 0.78 px at 13 px/em; between JetBrains Mono (0.02 em) and Cascadia (0.051 em) **[inference]** |
| Vertical extent of lines | descender − 0.10 em … ascender + 0.10 em, and at least 1.52 em in total | reaches the next line at line heights up to 1.5 × font size (VS Code editor on macOS), like JetBrains Mono (1.52) and Fira Code (1.54); Zed's 1.618 would need 0.15 em each side, which pokes further into neighbouring text rows **[inference]** |
| Block elements U+2580–259F, sextants, Powerline E0B0–E0B3 | exactly [0, advance] × [descender, ascender], no overshoot; halves split at the cell centre | JetBrains Mono, Iosevka, Fira Code; overshoot makes ▀/▄ unequal and shades overlap |
| Light stroke | equal to `post.underlineThickness` (see 5), about 0.06–0.09 em; the regular stem is the upper bound | references use 0.79–1.11 × stem; Ghostty and WezTerm draw their own boxes at the underline thickness, so equality makes font-drawn and terminal-drawn boxes match **[inference]** |
| Heavy stroke | 2 × light | 4 of 5 references; kitty, Ghostty, Alacritty, Windows Terminal, Neovide |
| Double lines | light / gap = light / light (3 × light overall) | 4 of 5 references |
| Thickness across the weight axis | constant | JetBrains Mono, Fira Code, DejaVu; terminal-drawn boxes ignore the bold attribute **[inference]** |
| Arc radius (centreline) | 0.42 × advance, never more than advance/2 | JetBrains Mono 0.42, Iosevka 0.41; Windows Terminal caps at half the smaller cell side |
| Dashes | period = advance/n horizontally and (ascender − descender)/n vertically, margin = gap/2, **no overshoot** on dashed glyphs | tiling in 4 of 5 references |
| Diagonals U+2571–2573 | centreline from cell corner to cell corner, stroke extended past the corners by the line overshoot | Iosevka, Fira Code, DejaVu; Ghostty and Alacritty enlarge their canvas for the same purpose |
| Coverage | all 128 + 32; Powerline E0A0–E0A2 and E0B0–E0B3 (7 glyphs, as JetBrains Mono and Fira Code); consider braille (256) and U+1FB00–1FB3B sextants | VTE draws neither braille nor Powerline; Zed draws no lines |

Add a build check: render `┼` and `█` grids at line heights 1.0, 1.2, 1.3, 1.35, 1.5 with the baseline centred as in a.2 and assert no gap.

### 4. Ligatures and features

- Expect ligatures to be **off** for many users: Alacritty, VTE and foot cannot show them; iTerm2, VS Code (editor and terminal) and JetBrains default to off. The unligated glyphs must be the primary design.
- Put programming ligatures in `calt` only. That is the feature kitty, Ghostty, WezTerm, Zed and VS Code's terminal name when they describe turning ligatures off, and iTerm2 has a dedicated `calt` switch.
- Build them the way kitty already recognises (d): one cell-advance glyph per input character, with empty spacer glyphs before the visible one (Fira Code) or after it (Cascadia). Name arbitrary-length arrow parts `*_start.seq`, `*_middle.seq`, `*_end.seq`.
- Keep the visible ligature glyph's ink inside its N cells (b.3: kitty and WezTerm rescale oversized glyphs).
- Offer alternates as `ss01`…/`cv01`…/`zero`: every configurable application accepts these tags (table in d). Document each with kitty's PostScript-name syntax, Ghostty's `font-feature`, WezTerm's `harfbuzz_features`, Windows Terminal's `features` object, VS Code's CSS string, Zed's object and Neovide's list.

### 5. Underline and strikethrough

- `post.underlineThickness` = 60 (0.06 em): with `ceil` rounding (kitty, Ghostty) it is 1 px up to 16 px/em and 2 px up to 33 px/em, which keeps Retina sizes at 2 px. It also sets Ghostty's and WezTerm's box-drawing thickness. The references use 0.026–0.050 em. **[inference]**
- `post.underlinePosition`: the **top** of the stroke per the spec, placed so that top − thickness stays above the descender; the references sit at −0.05 to −0.155 em. Remember FreeType-based terminals shift it down by half the thickness.
- `OS/2.yStrikeoutSize` = `underlineThickness` (the spec's recommendation); `yStrikeoutPosition` so that the stroke is centred near half the x-height. Only kitty on Linux, Ghostty, Alacritty (FreeType, DirectWrite), foot and Windows Terminal read it; WezTerm, VTE, Zed and kitty on macOS compute their own.
- Never ship 0 for either thickness: Ghostty treats that as a broken table.
- In the variable font, vary them through MVAR tags `undo`, `unds` only if box thickness is also meant to vary; with constant box thickness, keep them constant.

### 6. Variable font, static files, style linking

- Ship **both**: a variable TTF and static instances. Alacritty, WezTerm (named instances only), foot, Zed and JetBrains have no documented axis control.
- Named instances and static weights at steps fine enough to compensate for platform rendering (h): e.g. 300, 350, 400, 450, 500, 600, 700, 800. Cascadia has a SemiLight at 350; Fira Code's statics include Retina.
- fvar: a named instance called exactly `Regular` (kitty looks for it), `postScriptNameID` on every instance, name IDs 16/17.
- STAT: `wght` axis values in **format 1 or 2** named `Regular` and `Bold` (kitty ignores format 3 when matching names), plus `ital` values `Roman`/`Italic`. Test kitty's automatic bold on the result, because its name list puts `semibold` before `bold`.
- Separate upright and italic variable files, each with a `wght` axis, linked by family name and `ital` in STAT; kitty's `variable_name` key and its "best file via the OS matcher" step are written for exactly this layout.
- Do **not** add a `slnt` axis to the upright file unless −12 is a designed value: Windows Terminal sets `slnt = −12` for italic cells whenever the user has specified any axis.
- Style-link Regular/Bold/Italic/Bold Italic in the static family (name IDs 1/2, `fsSelection`, `macStyle`) with Bold at `usWeightClass` 700: VTE asks for weight + 300, Windows Terminal for 700, iTerm2 for at least 4 steps heavier on AppKit's 0–9 scale, Alacritty for the style name `Bold`.

### 7. Symbols

- Draw every symbol to fit **one** cell with the same advance; kitty and WezTerm shrink glyphs whose ink is wider than the cell, and xterm.js rescales overlapping ones.
- Prefer code points that are EAW N/Na and not emoji for anything our own TUI conventions rely on (f.2). Box drawing itself is EAW A, so it is single-cell only while "ambiguous is wide" is off; that is the default in every application examined.
- Include monochrome glyphs for the text-default emoji that TUIs use (`⚠ ✔ ✖ ▶ ◀ ⏸ ⏹ ⏺ ↩ ↪ ⬆ ⬇ ➡ ⬅ ☑ ♠ ♣ ♥ ♦`), so that the main font satisfies them before a colour-emoji fallback is consulted **[inference]**.
- Do not include single-cell glyphs for code points that are wide by the tables (`✅ ❌ ⭐ ⚡ ☰` …): terminals will allot two cells regardless.
- Private-use glyphs (Powerline E0A0–E0A2) must have ink no wider than one cell, or kitty will spread them over following spaces.

### 8. Weight

- Regular vertical stem in the references: 0.078–0.102 em; bold 0.111–0.168 em. Choose the regular for un-darkened FreeType rendering of light text on dark backgrounds, the thinnest common case, and let macOS users step down an instance **[inference]**.
- TrueType outlines with light or no hinting are what the examined Linux terminals actually request (Ghostty `light`, kitty per fontconfig, interpreter v40); stem darkening cannot be relied on (off by default in FreeType, and CFF-only where it exists).

---

## Gaps and disagreements

**Could not answer from primary sources**

- Which font tables DirectWrite reads for `DWRITE_FONT_METRICS.ascent/descent/lineGap`. The API page does not say; this affects Windows Terminal, Alacritty on Windows and Chromium on Windows.
- Apple Terminal: closed source. Cell computation, baseline, whether it draws any box glyphs itself, ligature and variable-font behaviour are unverified; only Apple's settings page and Textual's FAQ were available.
- JetBrains: I read the classic JediTerm source and the editor's settings page only. The 2025 terminal rewrite, JetBrains Runtime's variable-font support and how "Bold weight" maps to a variable font were not verified.
- iTerm2's variable-font axis handling and strikethrough metrics; Zed's and foot's axis selection; GTK/VTE font-variation syntax.
- Neovim GUIs other than Neovide.
- Whether kitty's automatic bold really lands on SemiBold for JetBrains Mono/Cascadia variable fonts (reasoned from code, not run).
- No rendering test was run for any claim in this report.

**Where sources disagree**

- WezTerm's `PolyStyle::OutlineHeavy` comment says "twice the thickness of underlines"; the code multiplies the stroke width by 3.01.
- WezTerm's doc says square-glyph overflow applies above aspect ratio 0.9; `glyphcache.rs` uses `aspect >= 0.7`.
- Alacritty's manual lists U+2500–259F, 1FB00–1FB3B and E0B0–E0B3 for the built-in font; the code also matches U+1FB82–1FB8B.
- Windows Terminal's schema says the default cell height is "usually quite close to" 1.2; Cascadia Code's typo line height measures 1.162 em.
- The FreeType property text reads as if stem darkening were on for CFF unless disabled; the source sets `no_stem_darkening = TRUE` for both CFF and the autofitter.
- `post.underlinePosition` is the top of the stroke in the spec and in Ghostty, but FreeType hands applications the centre, so the same value lands half a thickness apart.
- Neovide's reference text says `native` is the default box-drawing mode (and `settings.rs` agrees) while the sample config at the top of the same page shows `mode = "font-glyph"`.
- The reference fonts disagree with each other on every box-drawing choice except the horizontal centre (table b.2).

---

## Files

- Report: `/tmp/claude-0/-home-user-experiments/a86123d7-7ed9-5f3d-9952-1d096afee651/scratchpad/research/terminal-rendering.md`
- Measurement scripts: `/tmp/claude-0/-home-user-experiments/a86123d7-7ed9-5f3d-9952-1d096afee651/scratchpad/research/scripts/` (`measure.py`, `summ.py`, `table.py`, `arc.py`, `widths.py`)
- Raw measurements: `/tmp/claude-0/-home-user-experiments/a86123d7-7ed9-5f3d-9952-1d096afee651/scratchpad/research/measure_all.json`, `measure_summary.txt`, `ref_table.md`
- Downloaded sources: `/tmp/claude-0/-home-user-experiments/a86123d7-7ed9-5f3d-9952-1d096afee651/scratchpad/research/src/`; fonts in `fonts/ref/`; Unicode data in `ucd/`

[ft-sfobjs]: https://gitlab.freedesktop.org/freetype/freetype/-/raw/master/src/sfnt/sfobjs.c
[ft-driver]: https://gitlab.freedesktop.org/freetype/freetype/-/raw/master/include/freetype/ftdriver.h
[ft-cff]: https://gitlab.freedesktop.org/freetype/freetype/-/raw/master/src/cff/cffobjs.c
[ft-af]: https://gitlab.freedesktop.org/freetype/freetype/-/raw/master/src/autofit/afmodule.c
[ft-tt]: https://gitlab.freedesktop.org/freetype/freetype/-/raw/master/src/truetype/ttobjs.c
[ft-text]: https://freetype.org/freetype2/docs/hinting/text-rendering-general.html
[ft-props]: https://freetype.org/freetype2/docs/reference/ft2-properties.html
[hb-metrics]: https://raw.githubusercontent.com/harfbuzz/harfbuzz/main/src/hb-ot-metrics.cc
[fc-spacing]: https://gitlab.freedesktop.org/fontconfig/fontconfig/-/raw/main/src/fcfreetype.c
[skia-ft]: https://raw.githubusercontent.com/google/skia/main/src/ports/SkFontHost_FreeType.cpp
[skia-ct]: https://raw.githubusercontent.com/google/skia/main/src/ports/SkScalerContext_mac_ct.cpp
[skia-dw]: https://raw.githubusercontent.com/google/skia/main/src/ports/SkScalerContext_win_dw.cpp
[blink-fm]: https://raw.githubusercontent.com/chromium/chromium/main/third_party/blink/renderer/platform/fonts/font_metrics.cc
[blink-sfd]: https://raw.githubusercontent.com/chromium/chromium/main/third_party/blink/renderer/platform/fonts/simple_font_data.cc
[ot-recom]: https://learn.microsoft.com/en-us/typography/opentype/spec/recom
[ot-post]: https://learn.microsoft.com/en-us/typography/opentype/spec/post
[ot-os2]: https://learn.microsoft.com/en-us/typography/opentype/spec/os2
[dwrite-fm]: https://learn.microsoft.com/en-us/windows/win32/api/dwrite/ns-dwrite-dwrite_font_metrics
[uax11]: https://www.unicode.org/reports/tr11/
[eaw]: https://www.unicode.org/Public/UCD/latest/ucd/EastAsianWidth.txt
[emoji-data]: https://www.unicode.org/Public/UCD/latest/ucd/emoji/emoji-data.txt
[textual-mac]: https://raw.githubusercontent.com/Textualize/textual/main/questions/why-looks-bad-on-macos.question.md

[k-fonts]: https://raw.githubusercontent.com/kovidgoyal/kitty/master/kitty/fonts.c
[k-ft]: https://raw.githubusercontent.com/kovidgoyal/kitty/master/kitty/freetype.c
[k-ct]: https://raw.githubusercontent.com/kovidgoyal/kitty/master/kitty/core_text.m
[k-dec]: https://raw.githubusercontent.com/kovidgoyal/kitty/master/kitty/decorations.c
[k-def]: https://raw.githubusercontent.com/kovidgoyal/kitty/master/kitty/options/definition.py
[k-choose]: https://raw.githubusercontent.com/kovidgoyal/kitty/master/docs/kittens/choose-fonts.rst
[k-common]: https://raw.githubusercontent.com/kovidgoyal/kitty/master/kitty/fonts/common.py
[k-faq]: https://raw.githubusercontent.com/kovidgoyal/kitty/master/docs/faq.rst
[k-sizing]: https://raw.githubusercontent.com/kovidgoyal/kitty/master/docs/text-sizing-protocol.rst
[k-changelog]: https://raw.githubusercontent.com/kovidgoyal/kitty/master/docs/changelog.rst

[g-metrics]: https://raw.githubusercontent.com/ghostty-org/ghostty/main/src/font/Metrics.zig
[g-ft]: https://raw.githubusercontent.com/ghostty-org/ghostty/main/src/font/face/freetype.zig
[g-ct]: https://raw.githubusercontent.com/ghostty-org/ghostty/main/src/font/face/coretext.zig
[g-config]: https://raw.githubusercontent.com/ghostty-org/ghostty/main/src/config/Config.zig
[g-sprite]: https://raw.githubusercontent.com/ghostty-org/ghostty/main/src/font/sprite/Face.zig
[g-common]: https://raw.githubusercontent.com/ghostty-org/ghostty/main/src/font/sprite/draw/common.zig
[g-drawreadme]: https://raw.githubusercontent.com/ghostty-org/ghostty/main/src/font/sprite/draw/README.md
[g-resolver]: https://raw.githubusercontent.com/ghostty-org/ghostty/main/src/font/CodepointResolver.zig
[g-cell]: https://raw.githubusercontent.com/ghostty-org/ghostty/main/src/renderer/cell.zig
[g-generic]: https://raw.githubusercontent.com/ghostty-org/ghostty/main/src/renderer/generic.zig

[w-ftwrap]: https://raw.githubusercontent.com/wezterm/wezterm/main/wezterm-font/src/ftwrap.rs
[w-hb]: https://raw.githubusercontent.com/wezterm/wezterm/main/wezterm-font/src/shaper/harfbuzz.rs
[w-sprites]: https://raw.githubusercontent.com/wezterm/wezterm/main/wezterm-gui/src/utilsprites.rs
[w-cg]: https://raw.githubusercontent.com/wezterm/wezterm/main/wezterm-gui/src/customglyph.rs
[w-gc]: https://raw.githubusercontent.com/wezterm/wezterm/main/wezterm-gui/src/glyphcache.rs
[w-cbg]: https://raw.githubusercontent.com/wezterm/wezterm/main/docs/config/lua/config/custom_block_glyphs.md
[w-lh]: https://raw.githubusercontent.com/wezterm/wezterm/main/docs/config/lua/config/line_height.md
[w-cw]: https://raw.githubusercontent.com/wezterm/wezterm/main/docs/config/lua/config/cell_width.md
[w-shaping]: https://raw.githubusercontent.com/wezterm/wezterm/main/docs/config/font-shaping.md
[w-fonts]: https://raw.githubusercontent.com/wezterm/wezterm/main/docs/config/fonts.md
[w-font]: https://raw.githubusercontent.com/wezterm/wezterm/main/docs/config/lua/wezterm/font.md
[w-square]: https://raw.githubusercontent.com/wezterm/wezterm/main/docs/config/lua/config/allow_square_glyphs_to_overflow_width.md
[w-ambig]: https://raw.githubusercontent.com/wezterm/wezterm/main/docs/config/lua/config/treat_east_asian_ambiguous_width_as_wide.md
[w-strike]: https://raw.githubusercontent.com/wezterm/wezterm/main/docs/config/lua/config/strikethrough_position.md
[w-ftload]: https://raw.githubusercontent.com/wezterm/wezterm/main/docs/config/lua/config/freetype_load_target.md

[a-ft]: https://raw.githubusercontent.com/alacritty/crossfont/master/src/ft/mod.rs
[a-ct]: https://raw.githubusercontent.com/alacritty/crossfont/master/src/darwin/mod.rs
[a-dw]: https://raw.githubusercontent.com/alacritty/crossfont/master/src/directwrite/mod.rs
[a-display]: https://raw.githubusercontent.com/alacritty/alacritty/master/alacritty/src/display/mod.rs
[a-builtin]: https://raw.githubusercontent.com/alacritty/alacritty/master/alacritty/src/renderer/text/builtin_font.rs
[a-man]: https://raw.githubusercontent.com/alacritty/alacritty/master/extra/man/alacritty.5.scd
[a-changelog]: https://raw.githubusercontent.com/alacritty/alacritty/master/CHANGELOG.md

[i-ptv]: https://raw.githubusercontent.com/gnachman/iTerm2/master/sources/TerminalView/PTYTextView.m
[i-fse]: https://raw.githubusercontent.com/gnachman/iTerm2/master/sources/Fonts/FontSizeEstimator.m
[i-pfi]: https://raw.githubusercontent.com/gnachman/iTerm2/master/sources/Fonts/PTYFontInfo.m
[i-box]: https://raw.githubusercontent.com/gnachman/iTerm2/master/sources/Drawing/iTermBoxDrawingBezierCurveFactory.m
[i-adv]: https://raw.githubusercontent.com/gnachman/iTerm2/master/sources/Settings/iTermAdvancedSettingsModel.m
[i-doc]: https://iterm2.com/documentation-preferences-profiles-text.html

[wt-api]: https://raw.githubusercontent.com/microsoft/terminal/main/src/renderer/atlas/AtlasEngine.api.cpp
[wt-engine]: https://raw.githubusercontent.com/microsoft/terminal/main/src/renderer/atlas/AtlasEngine.cpp
[wt-bg]: https://raw.githubusercontent.com/microsoft/terminal/main/src/renderer/atlas/BuiltinGlyphs.cpp
[wt-bgh]: https://raw.githubusercontent.com/microsoft/terminal/main/src/renderer/atlas/BuiltinGlyphs.h
[wt-d3d]: https://raw.githubusercontent.com/microsoft/terminal/main/src/renderer/atlas/BackendD3D.cpp
[wt-schema]: https://raw.githubusercontent.com/microsoft/terminal/main/doc/cascadia/profiles.schema.json
[wt-docs]: https://raw.githubusercontent.com/MicrosoftDocs/terminal/main/TerminalDocs/customize-settings/profile-appearance.md

[v-fonts]: https://gitlab.gnome.org/GNOME/vte/-/raw/master/src/fonts-pangocairo.cc
[v-minifont]: https://gitlab.gnome.org/GNOME/vte/-/raw/master/src/minifont.cc
[v-cov]: https://gitlab.gnome.org/GNOME/vte/-/raw/master/src/minifont-coverage.py
[v-vte]: https://gitlab.gnome.org/GNOME/vte/-/raw/master/src/vte.cc
[v-draw]: https://gitlab.gnome.org/GNOME/vte/-/raw/master/src/drawing-context.cc
[v-defs]: https://gitlab.gnome.org/GNOME/vte/-/raw/master/src/vtedefines.hh

[f-ini]: https://codeberg.org/dnkl/foot/raw/branch/master/doc/foot.ini.5.scd
[f-term]: https://codeberg.org/dnkl/foot/raw/branch/master/terminal.c
[f-box]: https://codeberg.org/dnkl/foot/raw/branch/master/box-drawing.c
[f-fcft]: https://codeberg.org/dnkl/fcft/raw/branch/master/fcft.c

[x-charsize]: https://raw.githubusercontent.com/xtermjs/xterm.js/master/src/browser/services/CharSizeService.ts
[x-webgl]: https://raw.githubusercontent.com/xtermjs/xterm.js/master/addons/addon-webgl/src/WebglRenderer.ts
[x-webgl-d]: https://raw.githubusercontent.com/xtermjs/xterm.js/master/addons/addon-webgl/typings/addon-webgl.d.ts
[x-typings]: https://raw.githubusercontent.com/xtermjs/xterm.js/master/typings/xterm.d.ts
[x-lig]: https://raw.githubusercontent.com/xtermjs/xterm.js/master/addons/addon-ligatures/README.md
[x-atlas]: https://raw.githubusercontent.com/xtermjs/xterm.js/master/addons/addon-webgl/src/TextureAtlas.ts

[vs-termconf]: https://raw.githubusercontent.com/microsoft/vscode/main/src/vs/workbench/contrib/terminal/common/terminalConfiguration.ts
[vs-term]: https://raw.githubusercontent.com/microsoft/vscode/main/src/vs/workbench/contrib/terminal/common/terminal.ts
[vs-opts]: https://raw.githubusercontent.com/microsoft/vscode/main/src/vs/editor/common/config/editorOptions.ts
[vs-fontinfo]: https://raw.githubusercontent.com/microsoft/vscode/main/src/vs/editor/common/config/fontInfo.ts
[vs-fm]: https://raw.githubusercontent.com/microsoft/vscode/main/src/vs/editor/browser/config/fontMeasurements.ts

[z-term]: https://raw.githubusercontent.com/zed-industries/zed/main/crates/terminal_view/src/terminal_element.rs
[z-default]: https://raw.githubusercontent.com/zed-industries/zed/main/assets/settings/default.json
[z-line]: https://raw.githubusercontent.com/zed-industries/zed/main/crates/gpui/src/text_system/line.rs
[z-docs]: https://raw.githubusercontent.com/zed-industries/zed/main/docs/src/reference/all-settings.md

[n-shaper]: https://raw.githubusercontent.com/neovide/neovide/main/src/renderer/fonts/caching_shaper.rs
[n-boxset]: https://raw.githubusercontent.com/neovide/neovide/main/src/renderer/box_drawing/settings.rs
[n-boxr]: https://raw.githubusercontent.com/neovide/neovide/main/src/renderer/box_drawing/renderer.rs
[n-cfg]: https://raw.githubusercontent.com/neovide/neovide/main/website/docs/config-file.md

[j-font]: https://www.jetbrains.com/help/idea/settings-editor-font.html
[j-jedi]: https://raw.githubusercontent.com/JetBrains/jediterm/master/ui/src/com/jediterm/terminal/ui/TerminalPanel.java

[font-jbm]: https://raw.githubusercontent.com/JetBrains/JetBrainsMono/master/fonts/ttf/JetBrainsMono-Regular.ttf
[font-iosevka]: https://github.com/be5invis/Iosevka/releases/download/v33.2.5/PkgTTF-Iosevka-33.2.5.zip
[font-cascadia]: https://github.com/microsoft/cascadia-code/releases/download/v2407.24/CascadiaCode-2407.24.zip
[font-fira]: https://github.com/tonsky/FiraCode/releases/download/6.2/Fira_Code_v6.2.zip
[font-dejavu]: https://github.com/dejavu-fonts/dejavu-fonts/releases/download/version_2_37/dejavu-fonts-ttf-2.37.zip
