# Reference monospaced fonts: measured geometry

Measured on 2026-11-15 from the font files themselves with fontTools 4.68.0. 42 regular-weight fonts were measured; summary statistics use the 34 independent designs of the core set. Every length is in thousandths of the em, so it reads directly as units of a 1000-unit em. Ratios are dimensionless. The complete numbers for every font are in `ref_metrics.json` next to this file.

## The short version

- **Advance.** 19 of 34 core designs use a 600/1000 advance; the range is 500 (Iosevka, Inconsolata, Ubuntu Mono) to 700 (Martian Mono).
- **Proportions.** Median x-height 522 (Q1 496, Q3 536), cap height 700, x/cap 0.745, ascender 40 above the caps, descender -200. Figures are cap-height in 26 of 34.
- **Weight.** Median lowercase stem 84 (Q1 78.5, Q3 90), capital stem 86.8; stem / x-height 0.164. Horizontals are thinner: o top / o side 0.86, H bar / H stem 0.89, e bar / n stem 0.80.
- **Rhythm.** The n counter is 2.95 stems wide and the gap between two n is 0.71 of that counter. The m keeps its three stems at 0.94 of the n stem and its counters at 0.52 of the n counter.
- **Bowls.** The median o is close to an ellipse: diagonal fraction 0.731 (ellipse 0.707), superellipse exponent 2.21. JetBrains Mono is the squarish outlier of the callout set at 0.770 (exponent 2.66).
- **Operators.** + = < > share one centre line (median spread 1 unit) at 323, which is 0.62 of the x-height; the hyphen sits on it (median offset -0). Brackets are centred on it too (median offset 1).
- **Line.** Default line height (hhea) has median 1.20 em over the core set and 1.28 em over the 600-advance subset, range 1.00 to 1.48. 33 of 34 use a zero line gap, 30 have hhea equal to typo metrics, 24 set USE_TYPO_METRICS.
- **Box drawing.** Only 20 of 34 core designs ship U+2500. Where present, the light line is 79 thick (0.97 of the n stem), sits on the centre of the hhea line box (median offset -2), not on the math axis (median offset 8), and overhangs the advance by 10 per side.
- **Forms.** Zero is slashed in 20, dotted in 12 and plain in 2 of 34. Every font gives 1 a flag, l a top-left flag and I two serifs; l ends in a right tail in 19 and a full foot in 15.

## 1. What was measured, and how

### Fonts

Regular weight only. Variable fonts were pinned at wght=400 with `fontTools.varLib.instancer` (other axes at their defaults, except Recursive: MONO=1, CASL=0, slnt=0, CRSV=0.5, and wdth=100 where a width axis exists). Three sets:

- **core** (34 fonts): the families named in the brief that could be fetched, one per independent design. All medians and quartiles are over this set.
- **600 subset** (20 of the core): advance between 598 and 603, the fonts directly comparable with a 600-advance design.
- **dup** (4): measured, shown in the tables, kept out of the statistics because their outlines or metrics repeat a core font: Cascadia Mono (Cascadia Code without ligatures), Fira Mono (Fira Code within 1 unit), Hack (DejaVu Sans Mono metrics and stems), Liberation Mono (Cousine metrics).
- **extra** (4): Monaspace Neon, 0xProto, mononoki, B612 Mono. Measured and shown, not in the statistics, because the brief did not name them.

| font | file | source | upm | outlines | instance | usWeightClass | glyphs |
|---|---:|---:|---:|---:|---:|---:|---:|
| **JetBrains Mono** | `JetBrainsMono[wght].ttf` | [google/fonts](https://raw.githubusercontent.com/google/fonts/main/ofl/jetbrainsmono/JetBrainsMono%5Bwght%5D.ttf), upstream `19371302b9` | 1000 | glyf | wght=400 | 400 | 1179 |
| **IBM Plex Mono** | `IBMPlexMono-Regular.ttf` | [google/fonts](https://raw.githubusercontent.com/google/fonts/main/ofl/ibmplexmono/IBMPlexMono-Regular.ttf), upstream `9ab3b5b3b9` | 1000 | glyf | static | 400 | 1033 |
| **Source Code Pro** | `SourceCodePro[wght].ttf` | [google/fonts](https://raw.githubusercontent.com/google/fonts/main/ofl/sourcecodepro/SourceCodePro%5Bwght%5D.ttf), upstream `803b7e23ec` | 1000 | glyf | wght=400 | 400 | 1568 |
| **Fira Code** | `FiraCode[wght].ttf` | [google/fonts](https://raw.githubusercontent.com/google/fonts/main/ofl/firacode/FiraCode%5Bwght%5D.ttf), upstream `8da49d55f8` | 2000 | glyf | wght=400 | 400 | 1857 |
| **Cascadia Code** | `CascadiaCode[wght].ttf` | [google/fonts](https://raw.githubusercontent.com/google/fonts/main/ofl/cascadiacode/CascadiaCode%5Bwght%5D.ttf), upstream `56bcca3f2c` | 2048 | glyf | wght=400 | 400 | 4319 |
| **Commit Mono** | `CommitMono-400-Regular.otf` | [github.com](https://github.com/eigilnikolajsen/commit-mono/releases/download/v1.143/CommitMono-1.143.zip) | 1000 | CFF | static | 400 | 1932 |
| **Recursive Mono Linear** | `Recursive[CASL,CRSV,MONO,slnt,wght].ttf` | [google/fonts](https://raw.githubusercontent.com/google/fonts/main/ofl/recursive/Recursive%5BCASL%2CCRSV%2CMONO%2Cslnt%2Cwght%5D.ttf), upstream `071fc21f21` | 1000 | glyf | MONO=1, CASL=0, wght=400, slnt=0, CRSV=0.5 | 400 | 1304 |
| **Intel One Mono** | `IntelOneMono[wght].ttf` | [google/fonts](https://raw.githubusercontent.com/google/fonts/main/ofl/intelonemono/IntelOneMono%5Bwght%5D.ttf), upstream `06572f3e0b` | 1000 | glyf | wght=400 | 400 | 1059 |
| **DejaVu Sans Mono** | `DejaVuSansMono.ttf` | `/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf` (installed) | 2048 | glyf | static | 400 | 3377 |
| Roboto Mono | `RobotoMono[wght].ttf` | [google/fonts](https://raw.githubusercontent.com/google/fonts/main/ofl/robotomono/RobotoMono%5Bwght%5D.ttf), upstream `111eb14e36` | 2048 | glyf | wght=400 | 400 | 1006 |
| Red Hat Mono | `RedHatMono[wght].ttf` | [google/fonts](https://raw.githubusercontent.com/google/fonts/main/ofl/redhatmono/RedHatMono%5Bwght%5D.ttf), upstream `3228709780` | 1000 | glyf | wght=400 | 400 | 441 |
| Space Mono | `SpaceMono-Regular.ttf` | [google/fonts](https://raw.githubusercontent.com/google/fonts/main/ofl/spacemono/SpaceMono-Regular.ttf), upstream `329858c2c4` | 1000 | glyf | static | 400 | 765 |
| Ubuntu Mono | `UbuntuMono-Regular.ttf` | [google/fonts](https://raw.githubusercontent.com/google/fonts/main/ufl/ubuntumono/UbuntuMono-Regular.ttf), upstream `52f780bc9d` | 1000 | glyf | static | 400 | 1296 |
| Victor Mono | `VictorMono[wght].ttf` | [google/fonts](https://raw.githubusercontent.com/google/fonts/main/ofl/victormono/VictorMono%5Bwght%5D.ttf), upstream `8c00076e5a` | 1000 | glyf | wght=400 | 400 | 1442 |
| Geist Mono | `GeistMono[wght].ttf` | [google/fonts](https://raw.githubusercontent.com/google/fonts/main/ofl/geistmono/GeistMono%5Bwght%5D.ttf), upstream `77f0563c03` | 1000 | glyf | wght=400 | 400 | 1159 |
| Atkinson Hyperlegible Mono | `AtkinsonHyperlegibleMono[wght].ttf` | [google/fonts](https://raw.githubusercontent.com/google/fonts/main/ofl/atkinsonhyperlegiblemono/AtkinsonHyperlegibleMono%5Bwght%5D.ttf), upstream `154d503620` | 1000 | glyf | wght=400 | 400 | 380 |
| Martian Mono | `MartianMono[wdth,wght].ttf` | [google/fonts](https://raw.githubusercontent.com/google/fonts/main/ofl/martianmono/MartianMono%5Bwdth%2Cwght%5D.ttf), upstream `17865aac56` | 1000 | glyf | wght=400, wdth=100 | 400 | 567 |
| Inconsolata | `Inconsolata[wdth,wght].ttf` | [google/fonts](https://raw.githubusercontent.com/google/fonts/main/ofl/inconsolata/Inconsolata%5Bwdth%2Cwght%5D.ttf), upstream `fc1fc21081` | 1000 | glyf | wght=400, wdth=100 | 400 | 964 |
| Noto Sans Mono | `NotoSansMono[wdth,wght].ttf` | [google/fonts](https://raw.githubusercontent.com/google/fonts/main/ofl/notosansmono/NotoSansMono%5Bwdth%2Cwght%5D.ttf), upstream `9b7310b8f9` | 1000 | glyf | wght=400, wdth=100 | 400 | 3920 |
| Courier Prime | `CourierPrime-Regular.ttf` | [google/fonts](https://raw.githubusercontent.com/google/fonts/main/ofl/courierprime/CourierPrime-Regular.ttf), upstream `7fd585a2dd` | 2048 | glyf | static | 400 | 415 |
| DM Mono | `DMMono-Regular.ttf` | [google/fonts](https://raw.githubusercontent.com/google/fonts/main/ofl/dmmono/DMMono-Regular.ttf), upstream `57fadabfb2` | 1000 | glyf | static | 400 | 411 |
| Sometype Mono | `SometypeMono[wght].ttf` | [google/fonts](https://raw.githubusercontent.com/google/fonts/main/ofl/sometypemono/SometypeMono%5Bwght%5D.ttf), upstream `cf583c22bc` | 1000 | glyf | wght=400 | 400 | 563 |
| Fragment Mono | `FragmentMono-Regular.ttf` | [google/fonts](https://raw.githubusercontent.com/google/fonts/main/ofl/fragmentmono/FragmentMono-Regular.ttf), upstream `3ff027831f` | 1000 | glyf | static | 400 | 707 |
| Azeret Mono | `AzeretMono[wght].ttf` | [google/fonts](https://raw.githubusercontent.com/google/fonts/main/ofl/azeretmono/AzeretMono%5Bwght%5D.ttf), upstream `3d45a6c3e0` | 1000 | glyf | wght=400 | 400 | 646 |
| Spline Sans Mono | `SplineSansMono[wght].ttf` | [google/fonts](https://raw.githubusercontent.com/google/fonts/main/ofl/splinesansmono/SplineSansMono%5Bwght%5D.ttf), upstream `b167db03b7` | 2000 | glyf | wght=400 | 400 | 555 |
| Anonymous Pro | `AnonymousPro-Regular.ttf` | [google/fonts](https://raw.githubusercontent.com/google/fonts/main/ofl/anonymouspro/AnonymousPro-Regular.ttf), upstream `de345fb421` | 2048 | glyf | static | 400 | 624 |
| Overpass Mono | `OverpassMono[wght].ttf` | [google/fonts](https://raw.githubusercontent.com/google/fonts/main/ofl/overpassmono/OverpassMono%5Bwght%5D.ttf), upstream `c580d28bfa` | 2000 | glyf | wght=400 | 400 | 1801 |
| Oxygen Mono | `OxygenMono-Regular.ttf` | [google/fonts](https://raw.githubusercontent.com/google/fonts/main/ofl/oxygenmono/OxygenMono-Regular.ttf), upstream `62db0ebe34` | 2048 | glyf | static | 400 | 362 |
| Share Tech Mono | `ShareTechMono-Regular.ttf` | [google/fonts](https://raw.githubusercontent.com/google/fonts/main/ofl/sharetechmono/ShareTechMono-Regular.ttf), upstream `52f780bc9d` | 1000 | glyf | static | 400 | 268 |
| PT Mono | `PTM55FT.ttf` | [google/fonts](https://raw.githubusercontent.com/google/fonts/main/ofl/ptmono/PTM55FT.ttf) | 1000 | glyf | static | 400 | 808 |
| Cousine | `Cousine-Regular.ttf` | [google/fonts](https://raw.githubusercontent.com/google/fonts/main/ofl/cousine/Cousine-Regular.ttf), upstream `c0fbdb4384` | 2048 | glyf | static | 400 | 2396 |
| Go Mono | `Go-Mono.ttf` | [raw.githubusercontent.com](https://raw.githubusercontent.com/golang/image/master/font/gofont/ttfs/Go-Mono.ttf) | 2048 | glyf | static | 400 | 712 |
| Iosevka | `Iosevka-Regular.ttf` | [github.com](https://github.com/be5invis/Iosevka/releases/download/v33.2.5/PkgTTF-Iosevka-33.2.5.zip) | 1000 | glyf | static | 400 | 42613 |
| JuliaMono | `JuliaMono-Regular.ttf` | [raw.githubusercontent.com](https://raw.githubusercontent.com/cormullion/juliamono/master/JuliaMono-Regular.ttf) | 2000 | glyf | static | 400 | 12337 |
| Fira Mono (dup) | `FiraMono-Regular.ttf` | [google/fonts](https://raw.githubusercontent.com/google/fonts/main/ofl/firamono/FiraMono-Regular.ttf), upstream `a7d6892325` | 1000 | glyf | static | 400 | 1485 |
| Cascadia Mono (dup) | `CascadiaMono[wght].ttf` | [google/fonts](https://raw.githubusercontent.com/google/fonts/main/ofl/cascadiamono/CascadiaMono%5Bwght%5D.ttf), upstream `56bcca3f2c` | 2048 | glyf | wght=400 | 400 | 4319 |
| Liberation Mono (dup) | `LiberationMono-Regular.ttf` | `/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf` (installed) | 2048 | glyf | static | 400 | 2423 |
| Hack (dup) | `Hack-Regular.ttf` | [raw.githubusercontent.com](https://raw.githubusercontent.com/source-foundry/Hack/master/build/ttf/Hack-Regular.ttf) | 2048 | glyf | static | 400 | 1573 |
| Monaspace Neon (extra) | `MonaspaceNeon-Regular.otf` | [raw.githubusercontent.com](https://raw.githubusercontent.com/githubnext/monaspace/main/fonts/Static%20Fonts/Monaspace%20Neon/MonaspaceNeon-Regular.otf) | 2000 | CFF | static | 400 | 3606 |
| 0xProto (extra) | `0xProto-Regular.ttf` | [raw.githubusercontent.com](https://raw.githubusercontent.com/0xType/0xProto/main/fonts/0xProto-Regular.ttf) | 1000 | glyf | static | 400 | 863 |
| mononoki (extra) | `mononoki-Regular.ttf` | [raw.githubusercontent.com](https://raw.githubusercontent.com/madmalik/mononoki/main/export/mononoki-Regular.ttf) | 1024 | glyf | static | 400 | 932 |
| B612 Mono (extra) | `B612Mono-Regular.ttf` | [google/fonts](https://raw.githubusercontent.com/google/fonts/main/ofl/b612mono/B612Mono-Regular.ttf), upstream `48ac6ba67e` | 2000 | glyf | static | 400 | 590 |

Not reachable or not present: `apache/robotomono`, `apache/cousine` and `ofl/gomono` do not exist in google/fonts (Roboto Mono and Cousine are under `ofl/`; Go Mono came from golang/image); `ofl/commitmono` does not exist (Commit Mono came from its GitHub release). Iosevka came from the GitHub release archive `PkgTTF-Iosevka-33.2.5.zip`, so the npm route was not needed. Berkeley Mono, MonoLisa, Operator Mono, Input and other commercial fonts were not measured.

### Method

Each glyph is drawn through a fontTools pen that decomposes components and flattens every curve into 48 line segments; bounding boxes come from `BoundsPen` and are exact. A scan line is intersected with all edges and the filled intervals are found under the non-zero winding rule, so overlapping contours in variable-font instances are handled. Definitions:

- **x-height** is the top of `x`; **cap height** the top of `H`; **ascender** the tops of `l` and `b`; **descender** the bottoms of `p` and `g`; **figure height** the top of `1`.
- **Overshoot** is the bbox of `o`, `n`, `O`, `0` beyond those flat heights and beyond the baseline.
- **Vertical stems** are the filled interval of a horizontal scan: `l`, `I` at half their height, `n` at 0.40 of the x-height (left and right stems, and the counter between them), `H` at 0.25 of the cap height, `m` at 0.40 of the x-height.
- **Round side** of `o`, `O` is the first interval of a horizontal scan through the bbox centre; **top thickness** is the upper interval of a vertical scan through the bbox centre. **H bar** and **e bar** are the middle interval of a vertical scan through the centre; **t bar** is a vertical cut through the right arm of the bar.
- **Squareness** *f*: from the centre of the bbox towards each bbox corner, the fraction of the half-diagonal at which the outer contour is crossed, averaged over the four corners. An ellipse gives 0.7071, a rectangle 1.0. The superellipse exponent is n = ln 2 / ln(1/f). The inner value uses the counter's own box.
- **Math axis** is the mean of the bbox centres of `+ = < >`.
- **Line height** is (hhea ascender - hhea descender + hhea lineGap) / unitsPerEm; typo and win line heights are reported beside it. The **cell centre** is the middle of the hhea line box.
- **Box drawing**: bbox of U+2500, U+2502, U+2588, U+E0B0 against the advance and against the hhea ascender and descender.
- **Zero style** is classified by topology on a 240-pixel raster (ink components and enclosed holes) and confirmed by eye; **default ligatures** are found by shaping 22 ASCII sequences with HarfBuzz (uharfbuzz 0.57.0) and comparing with the unshaped glyphs.

Field meanings from the specification: OS/2 `sxHeight` "may be set equal to the top of the unscaled and unhinted glyph bounding box of the glyph encoded at U+0078" and `sCapHeight` likewise for U+0048 ([OpenType OS/2](https://learn.microsoft.com/en-us/typography/opentype/spec/os2)); `post.underlinePosition` is the "suggested y-coordinate of the top of the underline" ([OpenType post](https://learn.microsoft.com/en-us/typography/opentype/spec/post)).

## 2. Checks of the measuring code

1. **Outline x-height against OS/2 sxHeight.** 41 of the 42 fonts carry sxHeight (DejaVu Sans Mono has OS/2 version 1 and none). The measured top of `x` equals sxHeight to within 0.05 units in 38; the top of `H` equals sCapHeight in 38. The disagreements are in the fonts' own tables, not in the measurement: Ubuntu Mono x 464 vs sxHeight 520; Azeret Mono x 550 vs sxHeight 544; B612 Mono x 560 vs sxHeight 550; Source Code Pro H 656 vs sCapHeight 660; Ubuntu Mono H 619 vs sCapHeight 693; B612 Mono H 760 vs sCapHeight 750.

2. **Stems against the font's own PostScript hint values.** The fonts in google/fonts are TrueType, so I fetched CFF builds of three of them from their makers' repositories and read `StdVW` and `StdHW` from the CFF Private dictionary:

| font | StdVW | measured n | measured l | measured H | measured o side | StdHW | measured o top | measured H bar | StemSnapV | StemSnapH |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| [Source Code Pro (Adobe release OTF)](https://raw.githubusercontent.com/adobe-fonts/source-code-pro/release/OTF/SourceCodePro-Regular.otf) | 85 | 82 | 82 | 84 | 85 | 67 | 68 | 72 | 85 | 67 |
| [IBM Plex Mono (IBM/plex OTF)](https://raw.githubusercontent.com/IBM/plex/master/packages/plex-mono/fonts/complete/otf/IBMPlexMono-Regular.otf) | 80 | 80 | 80 | 84 | 85 | 68 | 69 | 73 | 68, 80, 89, 114 | 50, 62, 68, 73 |
| [Fira Mono (mozilla/Fira OTF)](https://raw.githubusercontent.com/mozilla/Fira/master/otf/FiraMono-Regular.otf) | 84 | 84 | 84 | 87 | 91 | 69 | 69 | 71 | 84 | 69 |

Fira Mono: StdVW 84 = measured n and l stem 84; StdHW 69 = measured o top 69. IBM Plex Mono: StdVW 80 = measured n and l stem 80; StdHW 68 against a measured o top of 69, and its StemSnapH lists 73, the measured H bar. Source Code Pro: StdVW 85 = measured o side 85 (n stem 82, H stem 84); StdHW 67 against a measured o top of 68. Commit Mono's OTF carries no StdVW, and Monaspace Neon's has only StdHW = 97, which equals its o side, so those two could not be used for this check.

3. **Static builds against my wght=400 instances.** Nine measurements (x, H, n stem, H stem, H bar, l stem, o side, o top, hyphen) were compared between the instanced variable font and an independently built static file: JetBrains Mono static Regular (JetBrains repo) vs VF@400: largest difference 0; Intel One Mono static Regular vs VF@400: largest difference 0; Source Code Pro static OTF vs VF@400: largest difference 0; IBM Plex Mono OTF vs google/fonts TTF: largest difference 0; Fira Mono OTF vs google/fonts TTF: largest difference 0.

4. **FreeType raster.** `l`, `H`, `n` and `x` were rendered with FreeType 2.14.3 at 1000 pixels per em and the pixel runs counted: IBM Plex Mono l 80 px vs 80, H 84 vs 84, n 80 vs 80, x-height 516 vs 516; Commit Mono l 84 px vs 84, H 87 vs 87, n 84 vs 84, x-height 540 vs 540; JetBrains Mono l 90 px vs 90, H 90 vs 90, n 90 vs 90, x-height 550 vs 550; DejaVu Sans Mono l 90 px vs 89.8, H 99 vs 99.1, n 90 vs 89.8, x-height 547 vs 546.9; Source Code Pro l 82 px vs 82, H 84 vs 84, n 82 vs 82, x-height 486 vs 486. All agree to rounding.

5. **A second implementation.** Another measurement script in this project (`research/cfd/measure.json`, written separately) covers 12 of the same fonts; x-height, cap height, n stem, H stem and H bar agree within 0.4 units, the other script's rounding.

## 3. Summary statistics with the nine called-out fonts

Minimum, quartiles, median and maximum over the core set (n = 34 unless a glyph is missing). "median (600 subset)" is the median over the 20 core fonts with a 600 advance. The Cascadia Code column is on its own 586 advance and Intel One Mono on 614.

### Em, advance and vertical proportions

| metric | min | Q1 | median | Q3 | max | n | median (600 subset) | JetBrains | Plex | Source Code | Fira Code | Cascadia | Commit | Recursive | Intel One | DejaVu |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| advance | 500 | 600 | **600** | 600 | 700 | 34 | 600 | 600 | 600 | 600 | 600 | 586 | 600 | 600 | 614 | 602 |
| x-height (x top) | 451 | 496 | **522** | 536 | 618 | 34 | 530 | 550 | 516 | 486 | 526 | 518 | 540 | 532 | 465 | 547 |
| cap height (H top) | 580 | 673 | **700** | 721 | 800 | 34 | 705 | 730 | 698 | 656 | 688 | 693 | 700 | 700 | 655 | 729 |
| ascender (l top) | 637 | 710 | **730** | 750 | 848 | 34 | 740 | 730 | 740 | 712 | 738 | 732 | 740 | 750 | 710 | 765 |
| ascender (b top) | 637 | 710 | **731** | 750 | 848 | 34 | 744 | 730 | 740 | 712 | 749 | 732 | 740 | 750 | 710 | 760 |
| descender (p bottom) | -240 | -210 | **-200** | -184 | -150 | 34 | -201 | -180 | -200 | -205 | -212 | -225 | -200 | -200 | -230 | -208 |
| descender (g bottom) | -250 | -223 | **-211** | -197 | -162 | 34 | -212 | -180 | -212 | -224 | -212 | -233 | -210 | -250 | -239 | -215 |
| figure height (1 top) | 592 | 673 | **700** | 722 | 800 | 34 | 710 | 730 | 698 | 638 | 688 | 693 | 700 | 710 | 666 | 729 |
| ascender - cap height | 0 | 20 | **40** | 51 | 74 | 34 | 41 | 0 | 42 | 56 | 60 | 39 | 40 | 50 | 55 | 31 |
| x-height / cap height | 0.697 | 0.725 | **0.745** | 0.753 | 0.802 | 34 | 0.750 | 0.753 | 0.739 | 0.741 | 0.765 | 0.747 | 0.771 | 0.760 | 0.710 | 0.750 |
| x-height / advance | 0.752 | 0.830 | **0.880** | 0.906 | 1.040 | 34 | 0.883 | 0.917 | 0.860 | 0.810 | 0.877 | 0.883 | 0.900 | 0.887 | 0.757 | 0.908 |
| cap height / advance | 0.967 | 1.138 | **1.167** | 1.210 | 1.470 | 34 | 1.175 | 1.217 | 1.163 | 1.093 | 1.147 | 1.183 | 1.167 | 1.167 | 1.067 | 1.211 |
| figure height / cap height | 0.973 | 1.000 | **1.000** | 1.000 | 1.025 | 34 | 1.000 | 1.000 | 1.000 | 0.973 | 1.000 | 1.000 | 1.000 | 1.014 | 1.017 | 1.000 |

### Overshoot

| metric | min | Q1 | median | Q3 | max | n | median (600 subset) | JetBrains | Plex | Source Code | Fira Code | Cascadia | Commit | Recursive | Intel One | DejaVu |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| overshoot: o above x | 0.0 | 10.0 | **11.0** | 12.0 | 16.1 | 34 | 11.0 | 8.0 | 12.0 | 12.0 | 11.0 | 9.8 | 10.0 | 11.0 | 15.0 | 13.2 |
| overshoot: o below baseline | 0.0 | 9.9 | **11.8** | 12.0 | 18.0 | 34 | 11.2 | 8.0 | 12.0 | 12.0 | 11.5 | 9.8 | 10.0 | 11.0 | 15.0 | 14.2 |
| overshoot: n above x | 0.0 | 10.0 | **11.0** | 12.0 | 16.1 | 34 | 11.2 | 10.0 | 12.0 | 12.0 | 11.0 | 9.8 | 10.0 | 11.0 | 7.0 | 13.2 |
| overshoot: O above cap | 0.0 | 10.4 | **12.0** | 14.0 | 20.0 | 34 | 12.0 | 10.0 | 12.0 | 12.0 | 11.0 | 9.8 | 10.0 | 20.0 | 15.0 | 13.2 |
| overshoot: O below baseline | 0.0 | 10.8 | **12.0** | 14.0 | 20.0 | 34 | 12.0 | 10.0 | 12.0 | 12.0 | 11.5 | 9.8 | 10.0 | 20.0 | 15.0 | 14.2 |
| overshoot: 0 above 1 | -1.5 | 8.8 | **10.5** | 12.0 | 16.0 | 34 | 11.0 | 10.0 | 12.0 | 12.0 | 11.0 | 9.8 | 10.0 | 10.0 | 4.0 | 13.2 |
| o top overshoot / x-height (%) | 0.00 | 1.87 | **2.24** | 2.41 | 3.23 | 34 | 2.15 | 1.45 | 2.33 | 2.47 | 2.09 | 1.89 | 1.85 | 2.07 | 3.23 | 2.41 |
| O top overshoot / cap height (%) | 0.00 | 1.57 | **1.72** | 1.96 | 2.86 | 34 | 1.71 | 1.37 | 1.72 | 1.83 | 1.60 | 1.41 | 1.43 | 2.86 | 2.29 | 1.81 |

### Line metrics and the cell

| metric | min | Q1 | median | Q3 | max | n | median (600 subset) | JetBrains | Plex | Source Code | Fira Code | Cascadia | Commit | Recursive | Intel One | DejaVu |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| hhea ascender | 781 | 906 | **957** | 1004 | 1120 | 34 | 984 | 1020 | 1025 | 984 | 990 | 928 | 900 | 950 | 1090 | 928 |
| hhea descender | -383 | -300 | **-260** | -231 | -170 | 34 | -274 | -300 | -275 | -273 | -322 | -234 | -200 | -250 | -290 | -236 |
| hhea lineGap | 0 | 0 | **0** | 0 | 70 | 34 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| line height hhea (em) | 1.000 | 1.157 | **1.200** | 1.310 | 1.481 | 34 | 1.278 | 1.320 | 1.300 | 1.257 | 1.312 | 1.162 | 1.100 | 1.200 | 1.380 | 1.164 |
| line height typo (em) | 0.907 | 1.157 | **1.200** | 1.310 | 1.481 | 34 | 1.278 | 1.320 | 1.300 | 1.257 | 1.312 | 1.162 | 1.100 | 1.200 | 1.380 | 1.200 |
| line height win (em) | 1.000 | 1.214 | **1.321** | 1.473 | 1.835 | 34 | 1.319 | 1.320 | 1.300 | 1.514 | 1.582 | 1.321 | 1.100 | 1.478 | 1.542 | 1.164 |
| cell aspect: line height / advance | 1.714 | 1.936 | **2.063** | 2.187 | 2.500 | 34 | 2.131 | 2.200 | 2.167 | 2.095 | 2.187 | 1.983 | 1.833 | 2.000 | 2.248 | 1.933 |
| room above cap in line box | 174 | 204 | **250** | 301 | 435 | 34 | 273 | 290 | 327 | 328 | 302 | 234 | 200 | 250 | 435 | 199 |
| room below p in line box | 0 | 33 | **62** | 95 | 180 | 34 | 68 | 120 | 75 | 68 | 110 | 10 | 0 | 50 | 60 | 28 |
| cell centre y | 220 | 331 | **350** | 366 | 425 | 34 | 355 | 360 | 375 | 356 | 334 | 347 | 350 | 350 | 400 | 346 |

### Stems and horizontals

| metric | min | Q1 | median | Q3 | max | n | median (600 subset) | JetBrains | Plex | Source Code | Fira Code | Cascadia | Commit | Recursive | Intel One | DejaVu |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| stem: n (left) | 66.9 | 78.5 | **84.0** | 90.0 | 110.0 | 34 | 85.8 | 90.0 | 80.0 | 82.0 | 84.0 | 103.5 | 84.0 | 92.0 | 86.0 | 89.8 |
| stem: l | 67.4 | 78.5 | **84.0** | 90.0 | 110.0 | 34 | 85.8 | 90.0 | 80.0 | 82.0 | 84.0 | 103.5 | 84.0 | 92.0 | 85.0 | 89.8 |
| stem: i | 67.4 | 80.0 | **84.0** | 90.0 | 110.0 | 34 | 85.8 | 90.0 | 80.0 | 82.0 | 84.0 | 103.5 | 84.0 | 92.0 | 86.0 | 89.8 |
| stem: H | 66.9 | 82.6 | **86.8** | 92.6 | 114.0 | 34 | 86.8 | 90.0 | 84.0 | 84.0 | 86.5 | 101.6 | 87.0 | 93.0 | 87.0 | 99.1 |
| stem: I | 67.4 | 82.2 | **87.0** | 93.2 | 114.0 | 34 | 88.0 | 92.0 | 84.0 | 84.0 | 88.0 | 101.6 | 87.0 | 94.0 | 87.0 | 99.1 |
| stem: m (outer) | 66.0 | 75.2 | **80.8** | 83.2 | 105.0 | 34 | 82.0 | 83.0 | 74.0 | 82.0 | 77.5 | 103.5 | 82.0 | 84.0 | 78.0 | 81.5 |
| round side: o | 66.9 | 83.1 | **87.0** | 90.2 | 109.0 | 34 | 88.5 | 90.0 | 85.0 | 85.0 | 90.0 | 107.4 | 85.0 | 91.0 | 87.0 | 95.2 |
| round side: O | 66.9 | 84.4 | **89.0** | 94.6 | 114.0 | 34 | 89.7 | 90.0 | 89.0 | 86.0 | 91.0 | 104.5 | 87.0 | 92.0 | 89.0 | 103.0 |
| horizontal: o top | 56.6 | 68.3 | **73.0** | 76.8 | 103.0 | 34 | 72.7 | 80.0 | 69.0 | 68.0 | 68.5 | 92.8 | 76.0 | 84.1 | 71.0 | 76.2 |
| horizontal: O top | 57.1 | 72.1 | **75.8** | 80.5 | 107.0 | 34 | 76.6 | 81.0 | 73.0 | 73.0 | 72.5 | 89.8 | 80.0 | 84.0 | 72.0 | 80.1 |
| horizontal: H bar | 57.1 | 70.2 | **76.3** | 81.5 | 108.0 | 34 | 76.3 | 82.0 | 73.0 | 72.0 | 71.0 | 92.8 | 80.0 | 84.0 | 73.0 | 83.0 |
| horizontal: e bar | 54.0 | 64.2 | **68.2** | 72.0 | 97.0 | 34 | 68.2 | 68.0 | 60.0 | 64.0 | 65.0 | 79.1 | 66.0 | 65.0 | 64.0 | 70.1 |
| horizontal: t bar | 57.1 | 67.0 | **69.8** | 75.0 | 103.0 | 34 | 69.5 | 82.0 | 68.0 | 67.0 | 65.0 | 90.8 | 75.0 | 81.0 | 72.0 | 69.8 |
| horizontal: hyphen | 57.1 | 72.0 | **75.8** | 80.0 | 100.0 | 34 | 75.8 | 80.0 | 84.0 | 62.0 | 73.0 | 90.8 | 76.0 | 89.0 | 83.0 | 80.1 |
| horizontal: underscore | 39.1 | 69.2 | **73.6** | 77.8 | 100.0 | 34 | 73.6 | 75.0 | 74.0 | 71.0 | 73.5 | 90.8 | 76.0 | 88.0 | 80.0 | 39.1 |
| n stem / x-height | 0.121 | 0.156 | **0.164** | 0.171 | 0.200 | 34 | 0.164 | 0.164 | 0.155 | 0.169 | 0.160 | 0.200 | 0.156 | 0.173 | 0.185 | 0.164 |
| n stem / advance | 0.122 | 0.134 | **0.140** | 0.153 | 0.177 | 34 | 0.143 | 0.150 | 0.133 | 0.137 | 0.140 | 0.177 | 0.140 | 0.153 | 0.140 | 0.149 |
| H stem / cap height | 0.094 | 0.120 | **0.125** | 0.133 | 0.152 | 34 | 0.125 | 0.123 | 0.120 | 0.128 | 0.126 | 0.146 | 0.124 | 0.133 | 0.133 | 0.136 |
| n stem / H stem | 0.892 | 0.960 | **0.977** | 1.000 | 1.062 | 34 | 0.983 | 1.000 | 0.952 | 0.976 | 0.971 | 1.019 | 0.966 | 0.989 | 0.989 | 0.906 |
| m stem / n stem | 0.889 | 0.918 | **0.942** | 0.988 | 1.029 | 34 | 0.935 | 0.922 | 0.925 | 1.000 | 0.923 | 1.000 | 0.976 | 0.913 | 0.907 | 0.908 |
| o side / n stem | 0.986 | 1.000 | **1.024** | 1.048 | 1.086 | 34 | 1.023 | 1.000 | 1.062 | 1.037 | 1.071 | 1.038 | 1.012 | 0.989 | 1.012 | 1.060 |
| O side / H stem | 0.986 | 1.000 | **1.024** | 1.046 | 1.081 | 34 | 1.034 | 1.000 | 1.060 | 1.024 | 1.052 | 1.028 | 1.000 | 0.989 | 1.023 | 1.039 |
| o top / o side | 0.578 | 0.808 | **0.861** | 0.901 | 0.945 | 34 | 0.826 | 0.889 | 0.812 | 0.800 | 0.761 | 0.864 | 0.894 | 0.924 | 0.816 | 0.800 |
| H bar / H stem | 0.629 | 0.851 | **0.890** | 0.910 | 0.977 | 34 | 0.897 | 0.911 | 0.869 | 0.857 | 0.821 | 0.913 | 0.919 | 0.903 | 0.839 | 0.838 |
| e bar / n stem | 0.622 | 0.753 | **0.800** | 0.882 | 0.934 | 34 | 0.781 | 0.756 | 0.750 | 0.780 | 0.774 | 0.764 | 0.786 | 0.707 | 0.744 | 0.781 |
| hyphen / n stem | 0.748 | 0.868 | **0.895** | 0.937 | 1.143 | 34 | 0.889 | 0.889 | 1.050 | 0.756 | 0.869 | 0.877 | 0.905 | 0.967 | 0.965 | 0.892 |
| H bar y-centre / cap height | 0.498 | 0.508 | **0.516** | 0.522 | 0.533 | 34 | 0.517 | 0.516 | 0.506 | 0.526 | 0.526 | 0.498 | 0.517 | 0.504 | 0.505 | 0.533 |
| e bar y-centre / x-height | 0.488 | 0.515 | **0.523** | 0.531 | 0.590 | 34 | 0.525 | 0.522 | 0.519 | 0.519 | 0.505 | 0.488 | 0.531 | 0.501 | 0.503 | 0.525 |
| t bar top - x-height | -39.1 | 0.0 | **0.0** | 0.0 | 5.0 | 34 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |

### Sidebearings, widths and counters

| metric | min | Q1 | median | Q3 | max | n | median (600 subset) | JetBrains | Plex | Source Code | Fira Code | Cascadia | Commit | Recursive | Intel One | DejaVu |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| lsb n | 18 | 80 | **88** | 96 | 113 | 34 | 90 | 92 | 98 | 93 | 100 | 82 | 107 | 93 | 95 | 95 |
| rsb n | 29 | 75 | **86** | 92 | 115 | 34 | 85 | 90 | 92 | 77 | 100 | 82 | 94 | 86 | 92 | 89 |
| lsb o (= rsb mostly) | -10 | 57 | **64** | 69 | 85 | 34 | 64 | 85 | 66 | 60 | 74 | 66 | 64 | 72 | 64 | 67 |
| lsb H | 24 | 62 | **69** | 79 | 98 | 34 | 69 | 93 | 80 | 79 | 84 | 68 | 66 | 73 | 92 | 67 |
| lsb O | -16 | 37 | **47** | 56 | 88 | 34 | 47 | 88 | 56 | 48 | 46 | 37 | 36 | 62 | 56 | 57 |
| lsb i | 54 | 80 | **92** | 106 | 145 | 34 | 92 | 85 | 106 | 90 | 120 | 78 | 108 | 86 | 114 | 87 |
| rsb i | 40 | 59 | **78** | 90 | 234 | 34 | 66 | 45 | 54 | 186 | 84 | 48 | 84 | 234 | 83 | 69 |
| lsb l | 30 | 60 | **74** | 85 | 130 | 34 | 69 | 30 | 80 | 81 | 60 | 48 | 65 | 68 | 59 | 78 |
| rsb l | 31 | 60 | **70** | 88 | 182 | 34 | 66 | 50 | 80 | 63 | 96 | 62 | 93 | 68 | 86 | 97 |
| lsb m | -2 | 41 | **48** | 53 | 76 | 34 | 47 | 66 | 54 | 58 | 50 | 55 | 41 | 48 | 53 | 53 |
| lsb w | -13 | 12 | **20** | 30 | 44 | 34 | 16 | 35 | 30 | 8 | 18 | 34 | 16 | 31 | 44 | 0 |
| lsb M | 12 | 42 | **52** | 64 | 98 | 34 | 54 | 76 | 68 | 72 | 30 | 62 | 42 | 64 | 62 | 42 |
| lsb W | -31 | 9 | **19** | 32 | 52 | 34 | 18 | 25 | 35 | 10 | 4 | 10 | -4 | 24 | 46 | 0 |
| lsb period | 172 | 218 | **226** | 238 | 263 | 34 | 226 | 217 | 226 | 219 | 212 | 221 | 223 | 222 | 220 | 239 |
| width n / advance | 0.665 | 0.691 | **0.711** | 0.731 | 0.889 | 34 | 0.711 | 0.697 | 0.683 | 0.717 | 0.667 | 0.720 | 0.665 | 0.702 | 0.695 | 0.694 |
| width o / advance | 0.691 | 0.774 | **0.788** | 0.809 | 0.873 | 34 | 0.787 | 0.717 | 0.780 | 0.800 | 0.755 | 0.773 | 0.787 | 0.760 | 0.791 | 0.778 |
| width H / advance | 0.680 | 0.736 | **0.762** | 0.794 | 0.900 | 34 | 0.768 | 0.690 | 0.733 | 0.737 | 0.722 | 0.767 | 0.780 | 0.757 | 0.700 | 0.778 |
| width O / advance | 0.707 | 0.814 | **0.843** | 0.879 | 0.907 | 34 | 0.843 | 0.707 | 0.813 | 0.840 | 0.845 | 0.873 | 0.880 | 0.793 | 0.818 | 0.810 |
| width i / advance | 0.467 | 0.677 | **0.705** | 0.758 | 0.814 | 34 | 0.735 | 0.783 | 0.733 | 0.540 | 0.658 | 0.785 | 0.680 | 0.467 | 0.679 | 0.741 |
| width l / advance | 0.500 | 0.701 | **0.741** | 0.789 | 0.893 | 34 | 0.749 | 0.867 | 0.733 | 0.760 | 0.739 | 0.813 | 0.737 | 0.773 | 0.764 | 0.709 |
| width m / advance | 0.780 | 0.830 | **0.840** | 0.859 | 1.025 | 34 | 0.848 | 0.780 | 0.820 | 0.833 | 0.832 | 0.813 | 0.870 | 0.840 | 0.829 | 0.832 |
| width w / advance | 0.858 | 0.896 | **0.930** | 0.953 | 1.016 | 34 | 0.948 | 0.883 | 0.900 | 0.973 | 0.942 | 0.883 | 0.947 | 0.894 | 0.858 | 1.000 |
| width M / advance | 0.680 | 0.787 | **0.802** | 0.853 | 0.959 | 34 | 0.818 | 0.747 | 0.773 | 0.760 | 0.898 | 0.787 | 0.860 | 0.787 | 0.798 | 0.859 |
| width W / advance | 0.804 | 0.901 | **0.938** | 0.967 | 1.016 | 34 | 0.940 | 0.917 | 0.883 | 0.967 | 0.985 | 0.967 | 1.013 | 0.917 | 0.850 | 1.000 |
| width 0 / width O | 0.810 | 0.917 | **0.956** | 0.995 | 1.038 | 34 | 0.962 | 1.038 | 1.000 | 0.909 | 0.889 | 0.924 | 0.901 | 0.971 | 0.956 | 0.968 |
| counter n | 196 | 233 | **250** | 265 | 291 | 34 | 248 | 238 | 250 | 266 | 232 | 215 | 231 | 237 | 255 | 238 |
| counter o | 203 | 279 | **301** | 315 | 346 | 34 | 299 | 250 | 298 | 310 | 273 | 238 | 302 | 274 | 312 | 278 |
| counter m (each) | 91 | 122 | **132** | 138 | 147 | 34 | 132 | 115 | 135 | 130 | 132 | 91 | 138 | 130 | 139 | 127 |
| counter H | 206 | 248 | **273** | 293 | 339 | 34 | 276 | 234 | 272 | 274 | 260 | 246 | 294 | 268 | 256 | 270 |
| n counter / n stem | 2.08 | 2.66 | **2.95** | 3.14 | 4.08 | 34 | 2.88 | 2.64 | 3.12 | 3.24 | 2.76 | 2.08 | 2.75 | 2.58 | 2.97 | 2.65 |
| gap between n n / n counter | 0.282 | 0.599 | **0.712** | 0.772 | 0.888 | 34 | 0.688 | 0.765 | 0.760 | 0.639 | 0.862 | 0.763 | 0.870 | 0.755 | 0.733 | 0.774 |
| m counter / n counter | 0.421 | 0.493 | **0.522** | 0.546 | 0.614 | 34 | 0.523 | 0.483 | 0.540 | 0.489 | 0.571 | 0.423 | 0.597 | 0.549 | 0.545 | 0.536 |

### Squareness of the bowls

| metric | min | Q1 | median | Q3 | max | n | median (600 subset) | JetBrains | Plex | Source Code | Fira Code | Cascadia | Commit | Recursive | Intel One | DejaVu |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| squareness o outer (f) | 0.712 | 0.723 | **0.731** | 0.736 | 0.818 | 34 | 0.731 | 0.770 | 0.730 | 0.719 | 0.735 | 0.738 | 0.717 | 0.751 | 0.722 | 0.743 |
| squareness o inner (f) | 0.716 | 0.728 | **0.735** | 0.749 | 0.869 | 34 | 0.741 | 0.795 | 0.767 | 0.725 | 0.752 | 0.740 | 0.721 | 0.767 | 0.727 | 0.747 |
| squareness O outer (f) | 0.721 | 0.732 | **0.738** | 0.750 | 0.836 | 34 | 0.737 | 0.806 | 0.750 | 0.729 | 0.736 | 0.750 | 0.721 | 0.788 | 0.737 | 0.753 |
| squareness O inner (f) | 0.717 | 0.732 | **0.747** | 0.757 | 0.880 | 34 | 0.748 | 0.835 | 0.775 | 0.731 | 0.755 | 0.750 | 0.727 | 0.815 | 0.745 | 0.768 |
| squareness 0 outer (f) | 0.716 | 0.735 | **0.744** | 0.751 | 0.829 | 34 | 0.745 | 0.799 | 0.750 | 0.737 | 0.744 | 0.750 | 0.735 | 0.768 | 0.738 | 0.747 |
| superellipse exponent o outer | 2.04 | 2.14 | **2.21** | 2.26 | 3.44 | 34 | 2.21 | 2.66 | 2.21 | 2.10 | 2.25 | 2.28 | 2.09 | 2.42 | 2.13 | 2.34 |
| superellipse exponent o inner | 2.07 | 2.19 | **2.25** | 2.40 | 4.94 | 34 | 2.30 | 3.03 | 2.62 | 2.16 | 2.43 | 2.30 | 2.12 | 2.61 | 2.17 | 2.38 |
| superellipse exponent O outer | 2.11 | 2.22 | **2.29** | 2.41 | 3.88 | 34 | 2.27 | 3.21 | 2.41 | 2.19 | 2.26 | 2.41 | 2.11 | 2.91 | 2.27 | 2.44 |
| o width / height | 0.704 | 0.830 | **0.870** | 0.934 | 0.999 | 34 | 0.864 | 0.760 | 0.867 | 0.941 | 0.825 | 0.844 | 0.843 | 0.823 | 0.982 | 0.816 |
| O width / height | 0.517 | 0.676 | **0.704** | 0.733 | 0.855 | 34 | 0.701 | 0.565 | 0.676 | 0.741 | 0.713 | 0.718 | 0.733 | 0.643 | 0.733 | 0.645 |

### Punctuation

| metric | min | Q1 | median | Q3 | max | n | median (600 subset) | JetBrains | Plex | Source Code | Fira Code | Cascadia | Commit | Recursive | Intel One | DejaVu |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| period width | 91 | 130 | **144** | 156 | 184 | 34 | 148 | 166 | 148 | 162 | 176 | 144 | 154 | 156 | 174 | 123 |
| period height | 91 | 135 | **146** | 156 | 191 | 34 | 148 | 166 | 138 | 169 | 176 | 144 | 154 | 153 | 162 | 149 |
| period width / n stem | 1.18 | 1.59 | **1.72** | 1.84 | 2.10 | 34 | 1.76 | 1.84 | 1.85 | 1.98 | 2.10 | 1.40 | 1.83 | 1.70 | 2.02 | 1.37 |
| comma bottom (depth) | -274 | -187 | **-165** | -145 | -120 | 34 | -161 | -160 | -141 | -213 | -180 | -213 | -158 | -200 | -152 | -140 |
| colon lower dot y-centre | 45 | 58 | **64** | 71 | 144 | 34 | 70 | 65 | 60 | 72 | 70 | 62 | 69 | 70 | 63 | 74 |
| colon upper dot y-centre | 366 | 431 | **450** | 462 | 562 | 34 | 458 | 485 | 456 | 430 | 430 | 455 | 471 | 462 | 400 | 445 |
| colon centre - math axis | -113 | -86 | **-61** | -42 | 4 | 34 | -58 | -55 | -47 | -80 | -62 | -87 | -40 | -34 | -93 | -54 |
| colon top - x-height | -57 | 0 | **8** | 13 | 42 | 34 | 10 | 10 | 9 | 29 | -16 | 10 | 8 | 7 | 13 | -28 |
| hyphen width | 220 | 310 | **367** | 401 | 566 | 34 | 361 | 320 | 290 | 430 | 401 | 488 | 388 | 362 | 374 | 254 |
| hyphen width / advance | 0.422 | 0.536 | **0.606** | 0.689 | 0.839 | 34 | 0.602 | 0.533 | 0.483 | 0.717 | 0.668 | 0.833 | 0.647 | 0.603 | 0.609 | 0.422 |
| hyphen y-centre | 234 | 276 | **307** | 329 | 400 | 34 | 303 | 330 | 304 | 330 | 313 | 346 | 310 | 300 | 328 | 274 |
| hyphen y-centre / x-height | 0.500 | 0.553 | **0.584** | 0.644 | 0.706 | 34 | 0.582 | 0.600 | 0.589 | 0.679 | 0.595 | 0.669 | 0.574 | 0.563 | 0.704 | 0.501 |
| hyphen y - math axis | -90 | -10 | **-0** | 0 | 4 | 34 | -1 | 0 | -1 | -1 | 1 | 0 | 0 | -0 | 3 | -40 |
| underscore top y | -197 | -95 | **-55** | -5 | 66 | 34 | -72 | -25 | -95 | -69 | -108 | 0 | -46 | -79 | -26 | -197 |
| underscore bottom y | -236 | -168 | **-130** | -89 | -20 | 34 | -138 | -100 | -169 | -140 | -182 | -91 | -122 | -167 | -106 | -236 |
| underscore width / advance | 0.733 | 0.771 | **0.833** | 1.000 | 1.046 | 34 | 0.812 | 0.800 | 0.800 | 0.800 | 0.833 | 0.833 | 0.767 | 0.783 | 0.746 | 1.000 |

### Operators and the math axis

| metric | min | Q1 | median | Q3 | max | n | median (600 subset) | JetBrains | Plex | Source Code | Fira Code | Cascadia | Commit | Recursive | Intel One | DejaVu |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| math axis (mean of + = < >) | 234 | 302 | **323** | 346 | 400 | 34 | 325 | 330 | 305 | 331 | 312 | 346 | 310 | 300 | 324 | 313 |
| math axis spread among + = < > | 0 | 0 | **1** | 8 | 22 | 34 | 1 | 0 | 1 | 2 | 3 | 0 | 0 | 1 | 6 | 0 |
| math axis / cap height | 0.366 | 0.432 | **0.462** | 0.499 | 0.508 | 34 | 0.464 | 0.452 | 0.437 | 0.505 | 0.454 | 0.499 | 0.443 | 0.428 | 0.495 | 0.430 |
| math axis / x-height | 0.500 | 0.573 | **0.620** | 0.675 | 0.714 | 34 | 0.616 | 0.600 | 0.592 | 0.681 | 0.593 | 0.669 | 0.574 | 0.564 | 0.697 | 0.573 |
| math axis - cell centre | -87 | -59 | **-30** | -2 | 96 | 34 | -27 | -30 | -70 | -24 | -22 | -0 | -40 | -50 | -76 | -33 |
| plus width | 372 | 447 | **472** | 489 | 566 | 34 | 473 | 470 | 476 | 430 | 469 | 488 | 468 | 462 | 474 | 516 |
| plus height | 386 | 456 | **478** | 505 | 566 | 34 | 478 | 470 | 486 | 452 | 468 | 507 | 468 | 461 | 480 | 517 |
| plus width / advance | 0.683 | 0.765 | **0.788** | 0.821 | 0.943 | 34 | 0.788 | 0.783 | 0.793 | 0.717 | 0.782 | 0.833 | 0.780 | 0.770 | 0.772 | 0.857 |
| plus stroke (horizontal bar) | 57.1 | 69.2 | **72.2** | 79.8 | 100.0 | 34 | 73.0 | 80.0 | 68.0 | 62.0 | 70.5 | 90.8 | 76.0 | 90.0 | 71.0 | 83.0 |
| equal width | 372 | 430 | **460** | 483 | 567 | 34 | 460 | 430 | 476 | 430 | 389 | 488 | 428 | 462 | 428 | 516 |
| equal width / advance | 0.648 | 0.728 | **0.766** | 0.806 | 0.945 | 34 | 0.766 | 0.717 | 0.793 | 0.717 | 0.648 | 0.833 | 0.713 | 0.770 | 0.697 | 0.857 |
| equal bar thickness | 57.1 | 69.2 | **72.7** | 79.9 | 100.0 | 34 | 73.5 | 80.0 | 68.0 | 62.0 | 73.0 | 90.8 | 74.0 | 89.0 | 72.0 | 84.0 |
| equal gap | 72 | 117 | **129** | 153 | 182 | 34 | 129 | 160 | 132 | 152 | 117 | 153 | 118 | 166 | 124 | 115 |
| equal gap / bar thickness | 1.00 | 1.60 | **1.72** | 1.99 | 2.76 | 34 | 1.73 | 2.00 | 1.94 | 2.45 | 1.60 | 1.69 | 1.59 | 1.87 | 1.72 | 1.37 |
| less width | 288 | 409 | **434** | 470 | 516 | 34 | 435 | 430 | 430 | 373 | 425 | 468 | 404 | 440 | 470 | 516 |
| less height | 399 | 485 | **513** | 566 | 733 | 34 | 545 | 530 | 578 | 568 | 561 | 483 | 508 | 567 | 484 | 489 |
| less width / advance | 0.527 | 0.693 | **0.740** | 0.790 | 0.857 | 34 | 0.725 | 0.717 | 0.717 | 0.622 | 0.708 | 0.798 | 0.673 | 0.733 | 0.765 | 0.857 |
| asterisk y-centre | 228 | 339 | **391** | 493 | 616 | 34 | 392 | 352 | 320 | 334 | 338 | 350 | 304 | 301 | 395 | 514 |
| asterisk y - math axis | -6 | 2 | **37** | 171 | 276 | 34 | 58 | 22 | 15 | 2 | 26 | 4 | -6 | 1 | 71 | 201 |

### Brackets and the bar

| metric | min | Q1 | median | Q3 | max | n | median (600 subset) | JetBrains | Plex | Source Code | Fira Code | Cascadia | Commit | Recursive | Intel One | DejaVu |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| bar | top | 652 | 730 | **762** | 836 | 1062 | 34 | 760 | 830 | 760 | 750 | 900 | 845 | 790 | 760 | 755 | 764 |
| bar | bottom | -378 | -214 | **-164** | -132 | -60 | 34 | -188 | -110 | -138 | -250 | -300 | -151 | -170 | -161 | -100 | -236 |
| bracket [ top | 670 | 710 | **766** | 819 | 945 | 34 | 766 | 830 | 760 | 708 | 816 | 798 | 790 | 756 | 787 | 760 |
| bracket [ bottom | -230 | -164 | **-145** | -121 | -66 | 34 | -150 | -110 | -138 | -152 | -116 | -104 | -170 | -148 | -135 | -132 |
| brace { top | 670 | 711 | **766** | 828 | 945 | 34 | 766 | 830 | 760 | 708 | 836 | 794 | 790 | 760 | 801 | 760 |
| brace { bottom | -230 | -169 | **-152** | -128 | -75 | 34 | -160 | -110 | -138 | -152 | -136 | -104 | -170 | -161 | -139 | -163 |
| paren ( top | 674 | 723 | **766** | 829 | 945 | 34 | 766 | 840 | 760 | 732 | 840 | 791 | 790 | 756 | 805 | 759 |
| paren ( bottom | -243 | -174 | **-152** | -126 | -74 | 34 | -152 | -120 | -138 | -176 | -140 | -98 | -170 | -141 | -147 | -132 |
| bracket height | 759 | 870 | **915** | 951 | 1090 | 34 | 923 | 940 | 898 | 860 | 931 | 902 | 960 | 904 | 922 | 892 |
| bracket top - cap height | 0 | 47 | **84** | 104 | 156 | 34 | 78 | 100 | 62 | 52 | 127 | 104 | 90 | 56 | 132 | 31 |
| bracket top - ascender (l) | -46 | 0 | **44** | 77 | 156 | 34 | 35 | 100 | 20 | -4 | 77 | 66 | 50 | 6 | 77 | -5 |
| bracket bottom - descender (p) | -30 | 28 | **51** | 78 | 149 | 34 | 50 | 70 | 62 | 53 | 96 | 120 | 30 | 52 | 95 | 76 |
| bracket centre - math axis | -106 | -24 | **1** | 23 | 39 | 34 | 0 | 30 | 6 | -53 | 38 | 0 | 0 | 4 | 2 | 1 |
| bracket centre - cap height/2 | -115 | -50 | **-38** | -6 | 25 | 34 | -39 | -5 | -38 | -50 | 6 | 0 | -40 | -46 | -2 | -50 |
| bracket stroke | 53.7 | 75.8 | **80.0** | 89.3 | 108.0 | 34 | 84.2 | 90.0 | 69.0 | 66.0 | 79.5 | 101.6 | 84.0 | 96.0 | 87.0 | 89.8 |
| bar | stroke | 67.0 | 72.8 | **78.3** | 84.0 | 106.0 | 34 | 76.5 | 90.0 | 70.0 | 74.0 | 75.0 | 101.6 | 78.0 | 96.0 | 80.0 | 84.0 |

### Underline and strikeout

| metric | min | Q1 | median | Q3 | max | n | median (600 subset) | JetBrains | Plex | Source Code | Fira Code | Cascadia | Commit | Recursive | Intel One | DejaVu |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| underline position (top, post) | -233 | -109 | **-100** | -75 | -20 | 34 | -100 | -155 | -140 | -50 | -50 | -49 | -100 | -193 | -75 | -20 |
| underline thickness (post) | 20 | 50 | **50** | 56 | 100 | 34 | 50 | 50 | 60 | 50 | 25 | 49 | 50 | 72 | 50 | 44 |
| strikeout position (OS/2) | 227 | 259 | **294** | 317 | 371 | 34 | 300 | 320 | 309 | 291 | 316 | 310 | 324 | 301 | 286 | 259 |
| strikeout size (OS/2) | 25 | 50 | **50** | 51 | 84 | 34 | 50 | 50 | 60 | 50 | 25 | 49 | 50 | 72 | 50 | 50 |
| strikeout position / x-height | 0.469 | 0.505 | **0.599** | 0.600 | 0.650 | 34 | 0.599 | 0.582 | 0.599 | 0.599 | 0.600 | 0.600 | 0.600 | 0.566 | 0.615 | 0.473 |

### Box drawing and blocks

| metric | min | Q1 | median | Q3 | max | n | median (600 subset) | JetBrains | Plex | Source Code | Fira Code | Cascadia | Commit | Recursive | Intel One | DejaVu |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| U+2500 thickness | 60 | 71 | **79** | 85 | 120 | 20 | 76 | 100 | 68 | 78 | 80 | 102 | 60 | – | 87 | 84 |
| U+2500 thickness / n stem | 0.71 | 0.84 | **0.97** | 1.00 | 1.71 | 20 | 0.95 | 1.11 | 0.85 | 0.95 | 0.95 | 0.98 | 0.71 | – | 1.01 | 0.94 |
| U+2500 y-centre | 275 | 305 | **335** | 350 | 400 | 20 | 344 | 370 | 300 | 300 | 350 | 345 | 350 | – | 330 | 344 |
| U+2500 y-centre - cell centre | -88 | -38 | **-2** | 3 | 40 | 20 | -2 | 10 | -75 | -56 | 16 | -2 | 0 | – | -70 | -2 |
| U+2500 y-centre - math axis | -64 | -2 | **8** | 38 | 85 | 20 | 9 | 40 | -5 | -31 | 38 | -1 | 40 | – | 6 | 30 |
| U+2500 overhang left | 0 | 4 | **10** | 24 | 80 | 20 | 10 | 20 | 34 | 39 | 5 | 51 | 10 | – | 20 | 10 |
| U+2500 overhang right | 0 | 4 | **10** | 24 | 80 | 20 | 10 | 20 | 34 | 39 | 5 | 51 | 10 | – | 20 | 10 |
| U+2502 thickness | 60 | 71 | **78** | 84 | 120 | 20 | 76 | 100 | 68 | 78 | 80 | 102 | 60 | – | 87 | 78 |
| U+2502 top - hhea ascender | -90 | 0 | **0** | 80 | 300 | 20 | 0 | 0 | -75 | 16 | 10 | 159 | 300 | – | -10 | 10 |
| U+2502 hhea descender - bottom | -47 | 0 | **37** | 142 | 300 | 20 | 50 | 0 | 75 | 127 | 178 | 24 | 300 | – | 130 | 14 |
| U+2502 height / hhea line | 0.899 | 1.000 | **1.014** | 1.147 | 1.546 | 20 | 1.008 | 1.000 | 1.000 | 1.114 | 1.143 | 1.158 | 1.546 | – | 1.087 | 1.021 |
| U+2588 overhang left | 0 | 0 | **0** | 0 | 10 | 18 | 0 | 10 | 0 | 0 | 0 | 0 | 0 | – | 0 | 10 |
| U+2588 top - hhea ascender | -96 | -34 | **0** | 7 | 175 | 18 | 0 | 0 | -75 | 16 | -90 | 159 | 0 | – | -70 | 10 |
| U+2588 hhea descender - bottom | -53 | 0 | **0** | 70 | 225 | 18 | 0 | 0 | 75 | 127 | -22 | 0 | 0 | – | 70 | 14 |

## 4. Per-font tables

Bold names are the nine called-out fonts. (dup) and (extra) rows are outside the statistics.

### 4.1 Em, advance, heights

| font | upm | advance | x | OS/2 sxHeight | cap (H) | asc l | asc b | asc d | desc p | desc q | desc g | desc y | fig 0 | fig 1 | x/cap | x/adv | cap/adv |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **JetBrains Mono** | 1000 | 600.0 | 550.0 | 550.0 | 730.0 | 730 | 730 | 730 | -180 | -180 | -180 | -180 | 740 | 730 | 0.753 | 0.917 | 1.217 |
| **IBM Plex Mono** | 1000 | 600.0 | 516.0 | 516.0 | 698.0 | 740 | 740 | 740 | -200 | -200 | -212 | -200 | 710 | 698 | 0.739 | 0.860 | 1.163 |
| **Source Code Pro** | 1000 | 600.0 | 486.0 | 486.0 | 656.0 | 712 | 712 | 712 | -205 | -205 | -224 | -209 | 650 | 638 | 0.741 | 0.810 | 1.093 |
| **Fira Code** | 2000 | 600.0 | 526.5 | 526.5 | 688.5 | 738 | 749 | 749 | -212 | -212 | -212 | -212 | 700 | 688 | 0.765 | 0.877 | 1.147 |
| **Cascadia Code** | 2048 | 585.9 | 517.6 | 517.6 | 693.4 | 732 | 732 | 732 | -225 | -225 | -233 | -234 | 703 | 693 | 0.747 | 0.883 | 1.183 |
| **Commit Mono** | 1000 | 600.0 | 540.0 | 540.0 | 700.0 | 740 | 740 | 740 | -200 | -200 | -210 | -205 | 710 | 700 | 0.771 | 0.900 | 1.167 |
| **Recursive Mono Linear** | 1000 | 600.0 | 532.0 | 532.0 | 700.0 | 750 | 750 | 750 | -200 | -200 | -250 | -200 | 720 | 710 | 0.760 | 0.887 | 1.167 |
| **Intel One Mono** | 1000 | 614.0 | 465.0 | 465.0 | 655.0 | 710 | 710 | 710 | -230 | -230 | -239 | -234 | 670 | 666 | 0.710 | 0.757 | 1.067 |
| **DejaVu Sans Mono** | 2048 | 602.1 | 546.9 | – | 729.0 | 765 | 760 | 760 | -208 | -210 | -215 | -208 | 742 | 729 | 0.750 | 0.908 | 1.211 |
| Roboto Mono | 2048 | 600.1 | 528.3 | 528.3 | 710.9 | 750 | 750 | 750 | -203 | -203 | -208 | -213 | 721 | 711 | 0.743 | 0.880 | 1.185 |
| Red Hat Mono | 1000 | 600.0 | 488.0 | 488.0 | 700.0 | 727 | 737 | 737 | -209 | -209 | -219 | -219 | 711 | 700 | 0.697 | 0.813 | 1.167 |
| Space Mono | 1000 | 612.0 | 496.0 | 496.0 | 700.0 | 700 | 700 | 700 | -200 | -200 | -200 | -200 | 714 | 700 | 0.709 | 0.810 | 1.144 |
| Ubuntu Mono | 1000 | 500.0 | 464.0 | 520.0 | 619.0 | 688 | 693 | 693 | -165 | -165 | -168 | -168 | 633 | 619 | 0.750 | 0.928 | 1.238 |
| Victor Mono | 1000 | 600.0 | 618.0 | 618.0 | 800.0 | 800 | 800 | 800 | -182 | -182 | -196 | -196 | 814 | 800 | 0.772 | 1.030 | 1.333 |
| Geist Mono | 1000 | 600.0 | 530.0 | 530.0 | 710.0 | 710 | 710 | 710 | -150 | -150 | -162 | -150 | 726 | 710 | 0.747 | 0.883 | 1.183 |
| Atkinson Hyperlegible Mono | 1000 | 632.0 | 496.0 | 496.0 | 668.0 | 708 | 708 | 708 | -162 | -174 | -191 | -162 | 682 | 668 | 0.743 | 0.785 | 1.057 |
| Martian Mono | 1000 | 700.0 | 600.0 | 600.0 | 800.0 | 848 | 848 | 848 | -200 | -200 | -216 | -216 | 816 | 800 | 0.750 | 0.857 | 1.143 |
| Inconsolata | 1000 | 500.0 | 457.0 | 457.0 | 623.0 | 665 | 665 | 665 | -167 | -167 | -172 | -174 | 627 | 624 | 0.734 | 0.914 | 1.246 |
| Noto Sans Mono | 1000 | 600.0 | 536.0 | 536.0 | 714.0 | 760 | 760 | 760 | -240 | -240 | -245 | -245 | 724 | 714 | 0.751 | 0.893 | 1.190 |
| Courier Prime | 2048 | 599.6 | 451.2 | 451.2 | 579.6 | 641 | 641 | 641 | -190 | -190 | -200 | -200 | 590 | 592 | 0.778 | 0.752 | 0.967 |
| DM Mono | 1000 | 600.0 | 496.0 | 496.0 | 700.0 | 720 | 720 | 720 | -220 | -220 | -232 | -220 | 712 | 700 | 0.709 | 0.827 | 1.167 |
| Sometype Mono | 1000 | 580.0 | 470.0 | 470.0 | 650.0 | 710 | 710 | 710 | -210 | -210 | -222 | -222 | 642 | 636 | 0.723 | 0.810 | 1.121 |
| Fragment Mono | 1000 | 618.0 | 524.0 | 524.0 | 699.0 | 729 | 729 | 729 | -218 | -218 | -218 | -218 | 715 | 707 | 0.750 | 0.848 | 1.131 |
| Azeret Mono | 1000 | 650.0 | 550.0 | 544.0 | 698.0 | 735 | 735 | 735 | -178 | -178 | -190 | -190 | 710 | 698 | 0.788 | 0.846 | 1.074 |
| Spline Sans Mono | 2000 | 600.0 | 545.5 | 545.5 | 727.0 | 778 | 778 | 778 | -202 | -202 | -226 | -216 | 742 | 727 | 0.750 | 0.909 | 1.212 |
| Anonymous Pro | 2048 | 545.9 | 455.1 | 455.1 | 637.2 | 637 | 637 | 637 | -182 | -182 | -193 | -193 | 648 | 637 | 0.714 | 0.834 | 1.167 |
| Overpass Mono | 2000 | 616.0 | 511.0 | 511.0 | 700.0 | 722 | 722 | 722 | -202 | -200 | -210 | -194 | 712 | 704 | 0.730 | 0.830 | 1.136 |
| Oxygen Mono | 2048 | 600.1 | 535.6 | 535.6 | 728.0 | 764 | 764 | 764 | -215 | -215 | -225 | -206 | 740 | 728 | 0.736 | 0.893 | 1.213 |
| Share Tech Mono | 1000 | 540.0 | 500.0 | 500.0 | 700.0 | 700 | 700 | 700 | -170 | -170 | -170 | -170 | 700 | 700 | 0.714 | 0.926 | 1.296 |
| PT Mono | 1000 | 600.0 | 500.0 | 500.0 | 700.0 | 700 | 700 | 700 | -200 | -200 | -212 | -205 | 712 | 700 | 0.714 | 0.833 | 1.167 |
| Cousine | 2048 | 600.1 | 528.3 | 528.3 | 658.7 | 725 | 725 | 725 | -208 | -208 | -207 | -208 | 669 | 659 | 0.802 | 0.880 | 1.098 |
| Go Mono | 2048 | 600.1 | 530.3 | 530.3 | 722.7 | 771 | 771 | 771 | -193 | -193 | -205 | -193 | 741 | 741 | 0.734 | 0.884 | 1.204 |
| Iosevka | 1000 | 500.0 | 520.0 | 520.0 | 735.0 | 735 | 735 | 735 | -215 | -215 | -223 | -215 | 743 | 735 | 0.708 | 1.040 | 1.470 |
| JuliaMono | 2000 | 600.0 | 550.0 | 550.0 | 725.0 | 790 | 790 | 790 | -190 | -191 | -210 | -199 | 735 | 725 | 0.759 | 0.917 | 1.208 |
| Fira Mono (dup) | 1000 | 600.0 | 527.0 | 527.0 | 689.0 | 739 | 749 | 749 | -212 | -212 | -212 | -212 | 700 | 689 | 0.765 | 0.878 | 1.148 |
| Cascadia Mono (dup) | 2048 | 585.9 | 517.6 | 517.6 | 693.4 | 732 | 732 | 732 | -225 | -225 | -233 | -234 | 703 | 693 | 0.747 | 0.883 | 1.183 |
| Liberation Mono (dup) | 2048 | 600.1 | 528.3 | 528.3 | 658.7 | 725 | 725 | 725 | -208 | -208 | -207 | -208 | 669 | 659 | 0.802 | 0.880 | 1.098 |
| Hack (dup) | 2048 | 602.1 | 546.9 | 546.9 | 729.0 | 760 | 760 | 760 | -208 | -210 | -215 | -208 | 742 | 729 | 0.750 | 0.908 | 1.211 |
| Monaspace Neon (extra) | 2000 | 620.0 | 513.5 | 513.5 | 730.0 | 776 | 765 | 765 | -194 | -194 | -206 | -206 | 742 | 730 | 0.703 | 0.828 | 1.177 |
| 0xProto (extra) | 1000 | 620.0 | 550.0 | 550.0 | 710.0 | 750 | 750 | 750 | -197 | -200 | -216 | -215 | 726 | 710 | 0.775 | 0.887 | 1.145 |
| mononoki (extra) | 1024 | 561.5 | 488.3 | 488.3 | 683.6 | 732 | 732 | 732 | -244 | -244 | -242 | -244 | 693 | 684 | 0.714 | 0.870 | 1.217 |
| B612 Mono (extra) | 2000 | 650.0 | 560.0 | 550.0 | 760.0 | 800 | 810 | 810 | -250 | -250 | -258 | -240 | 758 | 760 | 0.737 | 0.862 | 1.169 |

Observations. 8 of 34 core designs set the ascender equal to the cap height (JetBrains Mono, Space Mono, Victor Mono, Geist Mono, Anonymous Pro, Share Tech Mono, PT Mono, Iosevka); the rest raise it, by a median of 40. Figures differ from the cap height by more than 1 unit in Source Code Pro (638 vs 656), Recursive Mono Linear (710 vs 700), Intel One Mono (666 vs 655), Courier Prime (591.8 vs 579.6), Sometype Mono (636 vs 650), Fragment Mono (707 vs 699), Overpass Mono (703.5 vs 700), Go Mono (740.7 vs 722.7).

### 4.2 Overshoot

| font | o above x | o below base | n above x | O above cap | O below base | 0 above 1 | 0 below base | o top / x (%) | O top / cap (%) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **JetBrains Mono** | 8.0 | 8.0 | 10.0 | 10.0 | 10.0 | 10.0 | 10.0 | 1.45 | 1.37 |
| **IBM Plex Mono** | 12.0 | 12.0 | 12.0 | 12.0 | 12.0 | 12.0 | 12.0 | 2.33 | 1.72 |
| **Source Code Pro** | 12.0 | 12.0 | 12.0 | 12.0 | 12.0 | 12.0 | 12.0 | 2.47 | 1.83 |
| **Fira Code** | 11.0 | 11.5 | 11.0 | 11.0 | 11.5 | 11.0 | 11.5 | 2.09 | 1.60 |
| **Cascadia Code** | 9.8 | 9.8 | 9.8 | 9.8 | 9.8 | 9.8 | 9.8 | 1.89 | 1.41 |
| **Commit Mono** | 10.0 | 10.0 | 10.0 | 10.0 | 10.0 | 10.0 | 10.0 | 1.85 | 1.43 |
| **Recursive Mono Linear** | 11.0 | 11.0 | 11.0 | 20.0 | 20.0 | 10.0 | 20.0 | 2.07 | 2.86 |
| **Intel One Mono** | 15.0 | 15.0 | 7.0 | 15.0 | 15.0 | 4.0 | 15.0 | 3.23 | 2.29 |
| **DejaVu Sans Mono** | 13.2 | 14.2 | 13.2 | 13.2 | 14.2 | 13.2 | 14.2 | 2.41 | 1.81 |
| Roboto Mono | 9.8 | 9.8 | 9.8 | 9.8 | 9.8 | 10.3 | 9.8 | 1.86 | 1.38 |
| Red Hat Mono | 8.0 | 10.0 | 8.0 | 11.0 | 11.0 | 11.0 | 11.0 | 1.64 | 1.57 |
| Space Mono | 14.0 | 14.0 | 14.0 | 14.0 | 14.0 | 14.0 | 14.0 | 2.82 | 2.00 |
| Ubuntu Mono | 11.0 | 11.0 | 10.0 | 14.0 | 13.0 | 14.0 | 13.0 | 2.37 | 2.26 |
| Victor Mono | 14.0 | 14.0 | 14.0 | 14.0 | 14.0 | 14.0 | 14.0 | 2.27 | 1.75 |
| Geist Mono | 12.0 | 12.0 | 12.0 | 16.0 | 16.0 | 16.0 | 16.0 | 2.26 | 2.25 |
| Atkinson Hyperlegible Mono | 11.0 | 12.0 | 11.0 | 12.0 | 12.0 | 14.0 | 13.0 | 2.22 | 1.80 |
| Martian Mono | 16.0 | 16.0 | 16.0 | 16.0 | 16.0 | 16.0 | 16.0 | 2.67 | 2.00 |
| Inconsolata | 10.0 | 8.0 | 11.0 | 4.0 | 11.0 | 3.0 | 11.0 | 2.19 | 0.64 |
| Noto Sans Mono | 10.0 | 10.0 | 10.0 | 12.0 | 10.0 | 10.0 | 10.0 | 1.87 | 1.68 |
| Courier Prime | 10.7 | 10.7 | 10.7 | 10.7 | 10.7 | -1.5 | 10.7 | 2.37 | 1.85 |
| DM Mono | 12.0 | 12.0 | 12.0 | 12.0 | 12.0 | 12.0 | 12.0 | 2.42 | 1.71 |
| Sometype Mono | 12.0 | 12.0 | 12.0 | 12.0 | 12.0 | 6.0 | 12.0 | 2.55 | 1.85 |
| Fragment Mono | 16.0 | 18.0 | 15.0 | 16.0 | 18.0 | 8.0 | 18.0 | 3.05 | 2.29 |
| Azeret Mono | 12.0 | 12.0 | 12.0 | 12.0 | 12.0 | 12.0 | 12.0 | 2.18 | 1.72 |
| Spline Sans Mono | 11.0 | 7.5 | 11.5 | 14.5 | 15.0 | 14.5 | 15.0 | 2.02 | 1.99 |
| Anonymous Pro | 10.7 | 11.2 | 10.7 | 10.7 | 11.2 | 10.7 | 11.2 | 2.35 | 1.68 |
| Overpass Mono | 12.0 | 12.0 | 12.0 | 12.0 | 12.0 | 8.5 | 12.0 | 2.35 | 1.71 |
| Oxygen Mono | 16.1 | 12.2 | 16.1 | 12.2 | 12.2 | 11.7 | 12.2 | 3.01 | 1.68 |
| Share Tech Mono | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.00 | 0.00 |
| PT Mono | 12.0 | 12.0 | 12.0 | 12.0 | 12.0 | 12.0 | 12.0 | 2.40 | 1.71 |
| Cousine | 9.8 | 9.8 | 9.8 | 10.3 | 9.8 | 10.3 | 9.8 | 1.86 | 1.56 |
| Go Mono | 11.7 | 12.2 | 11.7 | 18.1 | 18.1 | 0.0 | 18.1 | 2.21 | 2.50 |
| Iosevka | 8.0 | 8.0 | 8.0 | 8.0 | 8.0 | 8.0 | 8.0 | 1.54 | 1.09 |
| JuliaMono | 10.0 | 6.0 | 10.0 | 10.0 | 12.0 | 10.0 | 10.0 | 1.82 | 1.38 |
| Fira Mono (dup) | 11.0 | 11.0 | 11.0 | 11.0 | 11.0 | 11.0 | 11.0 | 2.09 | 1.60 |
| Cascadia Mono (dup) | 9.8 | 9.8 | 9.8 | 9.8 | 9.8 | 9.8 | 9.8 | 1.89 | 1.41 |
| Liberation Mono (dup) | 9.8 | 9.8 | 9.8 | 10.3 | 9.8 | 10.3 | 9.8 | 1.86 | 1.56 |
| Hack (dup) | 13.2 | 14.2 | 13.2 | 13.2 | 14.2 | 13.2 | 14.2 | 2.41 | 1.81 |
| Monaspace Neon (extra) | 12.0 | 12.0 | 12.0 | 12.0 | 11.5 | 12.5 | 12.0 | 2.34 | 1.64 |
| 0xProto (extra) | 16.0 | 16.0 | 16.0 | 16.0 | 16.0 | 16.0 | 16.0 | 2.91 | 2.25 |
| mononoki (extra) | 11.7 | 11.7 | 9.8 | 9.8 | 9.8 | 9.8 | 9.8 | 2.40 | 1.43 |
| B612 Mono (extra) | -1.5 | 8.5 | 0.0 | -1.5 | 8.5 | -1.5 | 8.5 | -0.27 | -0.20 |

Fonts with no overshoot at all are the pixel-minded or geometric ones (Share Tech Mono). In most fonts the overshoot is the same at the baseline and at the x-height, and the capital overshoot is the same number of units as the lowercase one or one or two more.

### 4.3 Line metrics

| font | hhea asc | hhea desc | hhea gap | typo asc | typo desc | typo gap | win asc | win desc | USE_TYPO | line hhea | line typo | line win | cell h/w | cell centre y | room above cap | room below p |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **JetBrains Mono** | 1020 | -300 | 0 | 1020 | -300 | 0 | 1020 | 300 | yes | 1.320 | 1.320 | 1.320 | 2.200 | 360 | 290 | 120 |
| **IBM Plex Mono** | 1025 | -275 | 0 | 1025 | -275 | 0 | 1025 | 275 | yes | 1.300 | 1.300 | 1.300 | 2.167 | 375 | 327 | 75 |
| **Source Code Pro** | 984 | -273 | 0 | 984 | -273 | 0 | 1060 | 454 | yes | 1.257 | 1.257 | 1.514 | 2.095 | 356 | 328 | 68 |
| **Fira Code** | 990 | -322 | 0 | 990 | -322 | 0 | 1082 | 500 | yes | 1.312 | 1.312 | 1.582 | 2.187 | 334 | 302 | 110 |
| **Cascadia Code** | 928 | -234 | 0 | 928 | -234 | 0 | 1087 | 234 | yes | 1.162 | 1.162 | 1.321 | 1.983 | 347 | 234 | 10 |
| **Commit Mono** | 900 | -200 | 0 | 900 | -200 | 0 | 900 | 200 | no | 1.100 | 1.100 | 1.100 | 1.833 | 350 | 200 | 0 |
| **Recursive Mono Linear** | 950 | -250 | 0 | 950 | -250 | 0 | 1207 | 271 | yes | 1.200 | 1.200 | 1.478 | 2.000 | 350 | 250 | 50 |
| **Intel One Mono** | 1090 | -290 | 0 | 1090 | -290 | 0 | 1122 | 420 | yes | 1.380 | 1.380 | 1.542 | 2.248 | 400 | 435 | 60 |
| **DejaVu Sans Mono** | 928 | -236 | 0 | 760 | -240 | 200 | 928 | 236 | no | 1.164 | 1.200 | 1.164 | 1.933 | 346 | 199 | 28 |
| Roboto Mono | 1048 | -271 | 0 | 1048 | -271 | 0 | 1048 | 271 | no | 1.319 | 1.319 | 1.319 | 2.198 | 388 | 337 | 68 |
| Red Hat Mono | 1018 | -305 | 0 | 1018 | -305 | 0 | 1018 | 305 | yes | 1.323 | 1.323 | 1.323 | 2.205 | 356 | 318 | 96 |
| Space Mono | 1120 | -361 | 0 | 1120 | -361 | 0 | 1120 | 361 | yes | 1.481 | 1.481 | 1.481 | 2.420 | 380 | 420 | 161 |
| Ubuntu Mono | 830 | -170 | 0 | 693 | -165 | 49 | 830 | 170 | no | 1.000 | 0.907 | 1.000 | 2.000 | 330 | 211 | 5 |
| Victor Mono | 1100 | -250 | 0 | 1100 | -250 | 0 | 1306 | 529 | yes | 1.350 | 1.350 | 1.835 | 2.250 | 425 | 300 | 68 |
| Geist Mono | 1005 | -295 | 0 | 1005 | -295 | 0 | 1088 | 394 | yes | 1.300 | 1.300 | 1.482 | 2.167 | 355 | 295 | 145 |
| Atkinson Hyperlegible Mono | 984 | -316 | 0 | 984 | -316 | 0 | 996 | 411 | yes | 1.300 | 1.300 | 1.407 | 2.057 | 334 | 316 | 154 |
| Martian Mono | 1000 | -200 | 0 | 1000 | -200 | 0 | 1090 | 250 | yes | 1.200 | 1.200 | 1.340 | 1.714 | 400 | 200 | 0 |
| Inconsolata | 859 | -190 | 0 | 859 | -190 | 0 | 1004 | 454 | yes | 1.049 | 1.049 | 1.458 | 2.098 | 334 | 236 | 23 |
| Noto Sans Mono | 1069 | -293 | 0 | 1069 | -293 | 0 | 1229 | 389 | yes | 1.362 | 1.362 | 1.618 | 2.270 | 388 | 355 | 53 |
| Courier Prime | 781 | -342 | 0 | 781 | -342 | 0 | 928 | 391 | yes | 1.123 | 1.123 | 1.318 | 1.873 | 220 | 202 | 152 |
| DM Mono | 992 | -310 | 0 | 992 | -310 | 0 | 992 | 310 | no | 1.302 | 1.302 | 1.302 | 2.170 | 341 | 292 | 90 |
| Sometype Mono | 925 | -275 | 0 | 925 | -275 | 0 | 929 | 295 | yes | 1.200 | 1.200 | 1.224 | 2.069 | 325 | 275 | 65 |
| Fragment Mono | 950 | -250 | 0 | 950 | -250 | 0 | 945 | 265 | yes | 1.200 | 1.200 | 1.210 | 1.942 | 350 | 251 | 32 |
| Azeret Mono | 937 | -230 | 0 | 937 | -230 | 0 | 1112 | 230 | yes | 1.167 | 1.167 | 1.342 | 1.795 | 354 | 239 | 52 |
| Spline Sans Mono | 964 | -236 | 0 | 964 | -236 | 0 | 1080 | 311 | yes | 1.200 | 1.200 | 1.391 | 2.000 | 364 | 236 | 35 |
| Anonymous Pro | 818 | -182 | 0 | 818 | -182 | 0 | 818 | 182 | no | 1.000 | 1.000 | 1.000 | 1.832 | 318 | 181 | 0 |
| Overpass Mono | 883 | -383 | 0 | 883 | -383 | 0 | 1158 | 378 | yes | 1.266 | 1.266 | 1.536 | 2.055 | 250 | 183 | 180 |
| Oxygen Mono | 984 | -328 | 0 | 984 | -328 | 0 | 984 | 328 | no | 1.312 | 1.312 | 1.312 | 2.186 | 328 | 256 | 113 |
| Share Tech Mono | 885 | -242 | 0 | 885 | -242 | 0 | 885 | 242 | no | 1.127 | 1.127 | 1.127 | 2.087 | 322 | 185 | 72 |
| PT Mono | 885 | -235 | 0 | 885 | -235 | 0 | 885 | 235 | no | 1.120 | 1.120 | 1.120 | 1.867 | 325 | 185 | 35 |
| Cousine | 832 | -300 | 0 | 832 | -300 | 0 | 832 | 300 | yes | 1.133 | 1.133 | 1.133 | 1.888 | 266 | 174 | 93 |
| Go Mono | 945 | -211 | 0 | 771 | -193 | 192 | 945 | 211 | no | 1.156 | 1.156 | 1.156 | 1.926 | 367 | 222 | 18 |
| Iosevka | 965 | -215 | 70 | 965 | -285 | 0 | 965 | 285 | yes | 1.250 | 1.250 | 1.250 | 2.500 | 375 | 265 | 35 |
| JuliaMono | 950 | -225 | 0 | 950 | -225 | 0 | 1200 | 225 | yes | 1.175 | 1.175 | 1.425 | 1.958 | 362 | 225 | 35 |
| Fira Mono (dup) | 935 | -265 | 0 | 935 | -265 | 0 | 935 | 265 | yes | 1.200 | 1.200 | 1.200 | 2.000 | 335 | 246 | 53 |
| Cascadia Mono (dup) | 928 | -234 | 0 | 928 | -234 | 0 | 1087 | 234 | yes | 1.162 | 1.162 | 1.321 | 1.983 | 347 | 234 | 10 |
| Liberation Mono (dup) | 832 | -300 | 0 | 613 | -188 | 0 | 832 | 300 | no | 1.133 | 0.801 | 1.133 | 1.888 | 266 | 174 | 93 |
| Hack (dup) | 928 | -236 | 0 | 760 | -240 | 200 | 928 | 236 | no | 1.164 | 1.200 | 1.164 | 1.933 | 346 | 199 | 28 |
| Monaspace Neon (extra) | 945 | -200 | 100 | 945 | -200 | 100 | 945 | 250 | yes | 1.245 | 1.245 | 1.195 | 2.008 | 372 | 265 | 56 |
| 0xProto (extra) | 1130 | -430 | 0 | 1130 | -430 | 0 | 1130 | 430 | no | 1.560 | 1.560 | 1.560 | 2.516 | 350 | 420 | 233 |
| mononoki (extra) | 879 | -244 | 0 | 732 | -244 | 224 | 879 | 244 | no | 1.123 | 1.200 | 1.123 | 2.000 | 317 | 195 | 0 |
| B612 Mono (extra) | 965 | -250 | 0 | 965 | -250 | 0 | 983 | 356 | no | 1.215 | 1.215 | 1.339 | 1.869 | 358 | 205 | 0 |

The specification says of bit 7 of `fsSelection`: "If set, it is strongly recommended that applications use OS/2.sTypoAscender - OS/2.sTypoDescender + OS/2.sTypoLineGap as the default line spacing for this font" ([OpenType OS/2](https://learn.microsoft.com/en-us/typography/opentype/spec/os2)), and that the hhea values "are Apple specific" while the typo values "are used on the Windows platform, and are recommended for new text-layout implementations" ([OpenType hhea](https://learn.microsoft.com/en-us/typography/opentype/spec/hhea)). Google Fonts requires for new families that "Use_Typo_Metrics must be enabled", "Hhea and Typo metrics should be equal", "LineGap values must be 0" and that "the sum of the font's vertical metric values (absolute) should be 20-30% greater than the font's UPM" ([Google Fonts guide, vertical metrics](https://googlefonts.github.io/gf-guide/metrics.html)). Measured against that: hhea = typo in 30 of 34, zero hhea line gap in 33, USE_TYPO_METRICS set in 24, hhea line height inside 1.20 to 1.30 in 11 and above 1.30 in 10. Fonts whose three line heights disagree by more than 0.02 em: Source Code Pro (hhea 1.257, typo 1.257, win 1.514), Fira Code (hhea 1.312, typo 1.312, win 1.582), Cascadia Code (hhea 1.162, typo 1.162, win 1.321), Recursive Mono Linear (hhea 1.200, typo 1.200, win 1.478), Intel One Mono (hhea 1.380, typo 1.380, win 1.542), DejaVu Sans Mono (hhea 1.164, typo 1.200, win 1.164), Ubuntu Mono (hhea 1.000, typo 0.907, win 1.000), Victor Mono (hhea 1.350, typo 1.350, win 1.835), Geist Mono (hhea 1.300, typo 1.300, win 1.482), Atkinson Hyperlegible Mono (hhea 1.300, typo 1.300, win 1.407), Martian Mono (hhea 1.200, typo 1.200, win 1.340), Inconsolata (hhea 1.049, typo 1.049, win 1.458), Noto Sans Mono (hhea 1.362, typo 1.362, win 1.618), Courier Prime (hhea 1.123, typo 1.123, win 1.318), Sometype Mono (hhea 1.200, typo 1.200, win 1.224), Azeret Mono (hhea 1.167, typo 1.167, win 1.342), Spline Sans Mono (hhea 1.200, typo 1.200, win 1.391), Overpass Mono (hhea 1.266, typo 1.266, win 1.536), JuliaMono (hhea 1.175, typo 1.175, win 1.425).

### 4.4 Stems and contrast

| font | l | i | n left | n right | m outer | m middle | H | I | o side | O side | o top | O top | H bar | e bar | t bar | hyphen | underscore |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **JetBrains Mono** | 90.0 | 90.0 | 90.0 | 90.0 | 83.0 | 72.0 | 90.0 | 92.0 | 90.0 | 90.0 | 80.0 | 81.0 | 82.0 | 68.0 | 82.0 | 80.0 | 75.0 |
| **IBM Plex Mono** | 80.0 | 80.0 | 80.0 | 80.0 | 74.0 | 74.0 | 84.0 | 84.0 | 85.0 | 89.0 | 69.0 | 73.0 | 73.0 | 60.0 | 68.0 | 84.0 | 74.0 |
| **Source Code Pro** | 82.0 | 82.0 | 82.0 | 82.0 | 82.0 | 76.0 | 84.0 | 84.0 | 85.0 | 86.0 | 68.0 | 73.0 | 72.0 | 64.0 | 67.0 | 62.0 | 71.0 |
| **Fira Code** | 84.0 | 84.0 | 84.0 | 84.0 | 77.5 | 78.5 | 86.5 | 88.0 | 90.0 | 91.0 | 68.5 | 72.5 | 71.0 | 65.0 | 65.0 | 73.0 | 73.5 |
| **Cascadia Code** | 103.5 | 103.5 | 103.5 | 103.5 | 103.5 | 87.9 | 101.6 | 101.6 | 107.4 | 104.5 | 92.8 | 89.8 | 92.8 | 79.1 | 90.8 | 90.8 | 90.8 |
| **Commit Mono** | 84.0 | 84.0 | 84.0 | 84.0 | 82.0 | 82.0 | 87.0 | 87.0 | 85.0 | 87.0 | 76.0 | 80.0 | 80.0 | 66.0 | 75.0 | 76.0 | 76.0 |
| **Recursive Mono Linear** | 92.0 | 92.0 | 92.0 | 92.0 | 84.0 | 76.0 | 93.0 | 94.0 | 91.0 | 92.0 | 84.1 | 84.0 | 84.0 | 65.0 | 81.0 | 89.0 | 88.0 |
| **Intel One Mono** | 85.0 | 86.0 | 86.0 | 86.0 | 78.0 | 76.0 | 87.0 | 87.0 | 87.0 | 89.0 | 71.0 | 72.0 | 73.0 | 64.0 | 72.0 | 83.0 | 80.0 |
| **DejaVu Sans Mono** | 89.8 | 89.8 | 89.8 | 90.3 | 81.5 | 82.0 | 99.1 | 99.1 | 95.2 | 103.0 | 76.2 | 80.1 | 83.0 | 70.1 | 69.8 | 80.1 | 39.1 |
| Roboto Mono | 90.3 | 90.3 | 90.3 | 90.3 | 85.9 | 85.9 | 85.0 | 92.8 | 90.3 | 88.9 | 74.2 | 80.6 | 76.7 | 74.2 | 69.8 | 74.2 | 73.7 |
| Red Hat Mono | 73.0 | 73.0 | 73.0 | 73.0 | 68.0 | 67.0 | 77.0 | 77.0 | 72.0 | 78.0 | 65.0 | 70.0 | 67.0 | 54.0 | 60.0 | 60.0 | 57.0 |
| Space Mono | 78.0 | 78.0 | 78.0 | 78.0 | 78.0 | 78.0 | 84.0 | 84.0 | 80.0 | 84.0 | 74.0 | 78.0 | 78.0 | 72.0 | 72.0 | 72.0 | 72.0 |
| Ubuntu Mono | 82.0 | 82.0 | 83.0 | 82.0 | 75.0 | 75.0 | 82.0 | 82.0 | 85.0 | 84.0 | 73.0 | 71.0 | 70.0 | 67.0 | 69.0 | 78.0 | 70.0 |
| Victor Mono | 75.0 | 75.0 | 75.0 | 75.0 | 75.0 | 75.0 | 75.0 | 75.0 | 75.0 | 75.0 | 69.0 | 69.0 | 69.0 | 69.0 | 69.0 | 69.0 | 69.0 |
| Geist Mono | 84.0 | 84.0 | 84.0 | 84.0 | 84.0 | 84.0 | 86.0 | 86.0 | 88.0 | 90.0 | 80.0 | 84.0 | 84.0 | 74.0 | 74.0 | 79.0 | 78.0 |
| Atkinson Hyperlegible Mono | 85.0 | 86.0 | 85.0 | 86.0 | 76.0 | 76.0 | 88.0 | 88.0 | 87.0 | 87.0 | 70.0 | 73.0 | 77.0 | 59.0 | 67.0 | 79.0 | 77.0 |
| Martian Mono | 110.0 | 110.0 | 110.0 | 110.0 | 105.0 | 104.0 | 114.0 | 114.0 | 109.0 | 114.0 | 103.0 | 107.0 | 108.0 | 97.0 | 103.0 | 100.0 | 100.0 |
| Inconsolata | 73.0 | 72.0 | 70.0 | 70.0 | 66.0 | 67.0 | 73.0 | 70.0 | 76.0 | 72.0 | 60.0 | 61.0 | 60.0 | 56.0 | 59.0 | 67.0 | 61.0 |
| Noto Sans Mono | 90.0 | 90.0 | 90.0 | 90.0 | 80.0 | 80.0 | 90.0 | 90.0 | 89.0 | 92.0 | 73.0 | 80.0 | 80.0 | 72.0 | 75.0 | 80.0 | 80.0 |
| Courier Prime | 73.2 | 73.2 | 73.2 | 73.2 | 73.2 | 73.2 | 73.2 | 73.2 | 77.1 | 77.1 | 72.3 | 72.3 | 66.4 | 68.4 | 66.4 | 66.4 | 66.4 |
| DM Mono | 84.0 | 84.0 | 84.0 | 84.0 | 83.0 | 83.0 | 84.0 | 84.0 | 86.0 | 86.0 | 80.0 | 79.0 | 76.0 | 71.0 | 72.0 | 72.0 | 77.0 |
| Sometype Mono | 72.0 | 72.0 | 72.0 | 72.0 | 69.0 | 69.0 | 74.0 | 74.0 | 74.0 | 76.0 | 68.0 | 71.0 | 70.0 | 64.0 | 66.0 | 66.0 | 66.0 |
| Fragment Mono | 81.0 | 82.0 | 83.0 | 83.0 | 82.0 | 82.0 | 93.0 | 94.0 | 87.0 | 97.0 | 77.0 | 82.0 | 82.0 | 68.0 | 68.0 | 72.0 | 72.0 |
| Azeret Mono | 101.0 | 101.0 | 101.0 | 101.0 | 93.0 | 92.0 | 106.0 | 106.0 | 102.0 | 111.0 | 84.0 | 90.0 | 90.0 | 75.5 | 82.0 | 89.0 | 88.0 |
| Spline Sans Mono | 96.9 | 90.7 | 93.0 | 93.0 | 83.3 | 82.0 | 93.5 | 95.5 | 95.0 | 95.5 | 82.0 | 87.0 | 84.5 | 70.0 | 84.0 | 79.0 | 74.0 |
| Anonymous Pro | 67.4 | 67.4 | 66.9 | 67.4 | 66.9 | 67.4 | 66.9 | 67.4 | 66.9 | 66.9 | 56.6 | 57.1 | 57.1 | 57.1 | 57.1 | 57.1 | 57.1 |
| Overpass Mono | 81.0 | 81.5 | 81.5 | 81.0 | 80.0 | 80.5 | 82.5 | 82.0 | 83.5 | 85.5 | 74.5 | 75.5 | 77.5 | 72.0 | 72.5 | 78.5 | 81.5 |
| Oxygen Mono | 88.9 | 88.9 | 88.9 | 88.9 | 81.5 | 74.7 | 91.3 | 91.3 | 90.0 | 95.7 | 68.3 | 74.7 | 74.7 | 64.9 | 68.4 | 75.7 | 67.9 |
| Share Tech Mono | 85.0 | 85.0 | 85.0 | 85.0 | 80.0 | 80.0 | 87.0 | 87.0 | 85.0 | 87.0 | 75.0 | 76.0 | 74.0 | 75.0 | 75.0 | 75.0 | 75.0 |
| PT Mono | 78.0 | 80.0 | 77.0 | 78.0 | 76.0 | 76.0 | 83.0 | 83.0 | 83.0 | 88.0 | 67.0 | 74.0 | 74.0 | 70.0 | 67.0 | 74.0 | 70.0 |
| Cousine | 87.9 | 87.9 | 87.9 | 88.4 | 82.5 | 82.0 | 93.3 | 93.3 | 92.3 | 98.1 | 65.0 | 76.2 | 78.1 | 67.4 | 69.3 | 78.1 | 46.9 |
| Go Mono | 96.2 | 96.2 | 96.7 | 96.2 | 87.4 | 87.4 | 96.2 | 96.7 | 104.0 | 104.0 | 60.1 | 64.9 | 60.5 | 60.1 | 66.4 | 72.3 | 72.3 |
| Iosevka | 78.0 | 78.0 | 78.0 | 78.0 | 72.0 | 72.0 | 78.0 | 78.0 | 78.0 | 78.0 | 70.0 | 70.0 | 70.0 | 70.0 | 70.0 | 70.0 | 70.0 |
| JuliaMono | 87.5 | 87.5 | 87.5 | 87.5 | 90.0 | 90.0 | 87.0 | 88.0 | 88.0 | 89.4 | 73.0 | 77.0 | 79.0 | 76.0 | 75.0 | 100.0 | 86.0 |
| Fira Mono (dup) | 84.0 | 84.0 | 84.0 | 84.0 | 77.0 | 78.0 | 87.0 | 88.0 | 91.0 | 90.0 | 69.0 | 73.0 | 71.0 | 64.0 | 66.0 | 72.0 | 74.0 |
| Cascadia Mono (dup) | 103.5 | 103.5 | 103.5 | 103.5 | 103.5 | 87.9 | 101.6 | 101.6 | 107.4 | 104.5 | 92.8 | 89.8 | 92.8 | 79.1 | 90.8 | 90.8 | 90.8 |
| Liberation Mono (dup) | 87.9 | 87.9 | 87.9 | 88.4 | 82.5 | 82.0 | 93.3 | 93.3 | 92.3 | 98.1 | 65.0 | 76.2 | 78.1 | 67.4 | 69.3 | 78.1 | 46.9 |
| Hack (dup) | 89.8 | 89.8 | 89.8 | 90.3 | 81.5 | 82.0 | 99.1 | 99.1 | 95.2 | 103.0 | 76.2 | 80.1 | 83.0 | 70.3 | 69.8 | 80.1 | 58.6 |
| Monaspace Neon (extra) | 94.7 | 95.0 | 94.5 | 94.5 | 86.0 | 86.0 | 96.5 | 97.0 | 97.0 | 101.0 | 77.5 | 86.0 | 82.0 | 63.0 | 76.5 | 82.0 | 65.0 |
| 0xProto (extra) | 98.0 | 91.0 | 96.0 | 99.0 | 94.0 | 80.5 | 98.0 | 98.0 | 95.0 | 99.0 | 88.0 | 89.0 | 88.0 | 85.0 | 88.0 | 86.0 | 86.0 |
| mononoki (extra) | 83.0 | 83.0 | 83.0 | 83.0 | 83.0 | 83.0 | 83.0 | 83.0 | 83.0 | 83.0 | 75.2 | 74.2 | 75.2 | 75.2 | 74.2 | 75.2 | 75.2 |
| B612 Mono (extra) | 90.0 | 95.0 | 90.0 | 90.0 | 89.0 | 89.5 | 95.0 | 93.0 | 95.2 | 104.1 | 77.5 | 87.5 | 80.0 | 75.0 | 80.0 | 77.5 | 77.5 |

| font | n/x | n/adv | H/cap | n/H | m/n | o side/n | O side/H | o top/o side | H bar/H | e bar/n | hyphen/n | H bar y/cap | e bar y/x |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **JetBrains Mono** | 0.164 | 0.150 | 0.123 | 1.000 | 0.922 | 1.000 | 1.000 | 0.889 | 0.911 | 0.756 | 0.889 | 0.516 | 0.522 |
| **IBM Plex Mono** | 0.155 | 0.133 | 0.120 | 0.952 | 0.925 | 1.062 | 1.060 | 0.812 | 0.869 | 0.750 | 1.050 | 0.506 | 0.519 |
| **Source Code Pro** | 0.169 | 0.137 | 0.128 | 0.976 | 1.000 | 1.037 | 1.024 | 0.800 | 0.857 | 0.780 | 0.756 | 0.526 | 0.519 |
| **Fira Code** | 0.160 | 0.140 | 0.126 | 0.971 | 0.923 | 1.071 | 1.052 | 0.761 | 0.821 | 0.774 | 0.869 | 0.526 | 0.505 |
| **Cascadia Code** | 0.200 | 0.177 | 0.146 | 1.019 | 1.000 | 1.038 | 1.028 | 0.864 | 0.913 | 0.764 | 0.877 | 0.498 | 0.488 |
| **Commit Mono** | 0.156 | 0.140 | 0.124 | 0.966 | 0.976 | 1.012 | 1.000 | 0.894 | 0.919 | 0.786 | 0.905 | 0.517 | 0.531 |
| **Recursive Mono Linear** | 0.173 | 0.153 | 0.133 | 0.989 | 0.913 | 0.989 | 0.989 | 0.924 | 0.903 | 0.707 | 0.967 | 0.504 | 0.501 |
| **Intel One Mono** | 0.185 | 0.140 | 0.133 | 0.989 | 0.907 | 1.012 | 1.023 | 0.816 | 0.839 | 0.744 | 0.965 | 0.505 | 0.503 |
| **DejaVu Sans Mono** | 0.164 | 0.149 | 0.136 | 0.906 | 0.908 | 1.060 | 1.039 | 0.800 | 0.838 | 0.781 | 0.892 | 0.533 | 0.525 |
| Roboto Mono | 0.171 | 0.150 | 0.120 | 1.062 | 0.951 | 1.000 | 1.046 | 0.822 | 0.902 | 0.822 | 0.822 | 0.516 | 0.521 |
| Red Hat Mono | 0.150 | 0.122 | 0.110 | 0.948 | 0.931 | 0.986 | 1.013 | 0.903 | 0.870 | 0.740 | 0.822 | 0.504 | 0.523 |
| Space Mono | 0.157 | 0.128 | 0.120 | 0.929 | 1.000 | 1.026 | 1.000 | 0.925 | 0.929 | 0.923 | 0.923 | 0.501 | 0.524 |
| Ubuntu Mono | 0.179 | 0.166 | 0.133 | 1.012 | 0.904 | 1.024 | 1.024 | 0.859 | 0.854 | 0.807 | 0.940 | 0.522 | 0.525 |
| Victor Mono | 0.121 | 0.125 | 0.094 | 1.000 | 1.000 | 1.000 | 1.000 | 0.920 | 0.920 | 0.920 | 0.920 | 0.529 | 0.536 |
| Geist Mono | 0.159 | 0.140 | 0.121 | 0.977 | 1.000 | 1.048 | 1.046 | 0.909 | 0.977 | 0.881 | 0.941 | 0.503 | 0.521 |
| Atkinson Hyperlegible Mono | 0.171 | 0.135 | 0.132 | 0.966 | 0.894 | 1.024 | 0.989 | 0.805 | 0.875 | 0.694 | 0.929 | 0.516 | 0.529 |
| Martian Mono | 0.183 | 0.157 | 0.142 | 0.965 | 0.955 | 0.991 | 1.000 | 0.945 | 0.947 | 0.882 | 0.909 | 0.504 | 0.521 |
| Inconsolata | 0.153 | 0.140 | 0.117 | 0.959 | 0.943 | 1.086 | 0.986 | 0.789 | 0.822 | 0.800 | 0.957 | 0.525 | 0.538 |
| Noto Sans Mono | 0.168 | 0.150 | 0.126 | 1.000 | 0.889 | 0.989 | 1.022 | 0.820 | 0.889 | 0.800 | 0.889 | 0.522 | 0.535 |
| Courier Prime | 0.162 | 0.122 | 0.126 | 1.000 | 1.000 | 1.053 | 1.053 | 0.938 | 0.907 | 0.934 | 0.907 | 0.516 | 0.536 |
| DM Mono | 0.169 | 0.140 | 0.120 | 1.000 | 0.988 | 1.024 | 1.024 | 0.930 | 0.905 | 0.845 | 0.857 | 0.514 | 0.533 |
| Sometype Mono | 0.153 | 0.124 | 0.114 | 0.973 | 0.958 | 1.028 | 1.027 | 0.919 | 0.946 | 0.889 | 0.917 | 0.509 | 0.515 |
| Fragment Mono | 0.158 | 0.134 | 0.133 | 0.892 | 0.988 | 1.048 | 1.043 | 0.885 | 0.882 | 0.819 | 0.868 | 0.512 | 0.517 |
| Azeret Mono | 0.184 | 0.155 | 0.152 | 0.953 | 0.921 | 1.010 | 1.047 | 0.824 | 0.849 | 0.748 | 0.881 | 0.519 | 0.590 |
| Spline Sans Mono | 0.171 | 0.155 | 0.129 | 0.995 | 0.896 | 1.022 | 1.021 | 0.863 | 0.904 | 0.753 | 0.850 | 0.513 | 0.531 |
| Anonymous Pro | 0.147 | 0.122 | 0.105 | 1.000 | 1.000 | 1.000 | 1.000 | 0.846 | 0.854 | 0.854 | 0.854 | 0.508 | 0.511 |
| Overpass Mono | 0.160 | 0.132 | 0.118 | 0.988 | 0.982 | 1.024 | 1.036 | 0.892 | 0.939 | 0.883 | 0.963 | 0.519 | 0.507 |
| Oxygen Mono | 0.166 | 0.148 | 0.125 | 0.974 | 0.917 | 1.012 | 1.048 | 0.759 | 0.818 | 0.730 | 0.852 | 0.522 | 0.535 |
| Share Tech Mono | 0.170 | 0.157 | 0.124 | 0.977 | 0.941 | 1.000 | 1.000 | 0.882 | 0.851 | 0.882 | 0.882 | 0.513 | 0.505 |
| PT Mono | 0.154 | 0.128 | 0.119 | 0.928 | 0.987 | 1.078 | 1.060 | 0.807 | 0.892 | 0.909 | 0.961 | 0.511 | 0.544 |
| Cousine | 0.166 | 0.146 | 0.142 | 0.942 | 0.939 | 1.050 | 1.051 | 0.704 | 0.837 | 0.767 | 0.888 | 0.521 | 0.529 |
| Go Mono | 0.182 | 0.161 | 0.133 | 1.005 | 0.904 | 1.075 | 1.081 | 0.578 | 0.629 | 0.622 | 0.748 | 0.517 | 0.523 |
| Iosevka | 0.150 | 0.156 | 0.106 | 1.000 | 0.923 | 1.000 | 1.000 | 0.897 | 0.897 | 0.897 | 0.897 | 0.517 | 0.500 |
| JuliaMono | 0.159 | 0.146 | 0.120 | 1.006 | 1.029 | 1.006 | 1.028 | 0.830 | 0.908 | 0.869 | 1.143 | 0.526 | 0.525 |
| Fira Mono (dup) | 0.159 | 0.140 | 0.126 | 0.966 | 0.917 | 1.083 | 1.034 | 0.758 | 0.816 | 0.762 | 0.857 | 0.526 | 0.505 |
| Cascadia Mono (dup) | 0.200 | 0.177 | 0.146 | 1.019 | 1.000 | 1.038 | 1.028 | 0.864 | 0.913 | 0.764 | 0.877 | 0.498 | 0.488 |
| Liberation Mono (dup) | 0.166 | 0.146 | 0.142 | 0.942 | 0.939 | 1.050 | 1.051 | 0.704 | 0.837 | 0.767 | 0.888 | 0.521 | 0.529 |
| Hack (dup) | 0.164 | 0.149 | 0.136 | 0.906 | 0.908 | 1.060 | 1.039 | 0.800 | 0.838 | 0.783 | 0.892 | 0.533 | 0.525 |
| Monaspace Neon (extra) | 0.184 | 0.152 | 0.132 | 0.979 | 0.910 | 1.026 | 1.047 | 0.799 | 0.850 | 0.667 | 0.868 | 0.513 | 0.555 |
| 0xProto (extra) | 0.174 | 0.155 | 0.138 | 0.980 | 0.979 | 0.990 | 1.010 | 0.926 | 0.898 | 0.885 | 0.896 | 0.521 | 0.474 |
| mononoki (extra) | 0.170 | 0.148 | 0.121 | 1.000 | 1.000 | 1.000 | 1.000 | 0.906 | 0.906 | 0.906 | 0.906 | 0.531 | 0.551 |
| B612 Mono (extra) | 0.161 | 0.139 | 0.125 | 0.947 | 0.989 | 1.058 | 1.096 | 0.814 | 0.842 | 0.833 | 0.861 | 0.530 | 0.513 |

Observations. The pattern in the humanist and grotesque designs is: capital stem a few units heavier than the lowercase stem, round sides 2 to 6 percent heavier than straight stems, horizontals 10 to 20 percent lighter than verticals, and the e bar the thinnest stroke in the font. The m is fitted by thinning its stems (median 0.94 of the n stem) and halving its counters; 7 of 34 keep the full stem. Strictly monoline designs (Victor Mono, Iosevka, mononoki, Anonymous Pro) keep one vertical and one horizontal value everywhere.

### 4.5 Sidebearings, widths, counters

Left (L) and right (R) sidebearings.

| font | n L | n R | o L | o R | H L | H R | O L | O R | i L | i R | l L | l R | m L | m R | w L | w R | M L | M R | W L | W R | . L | . R |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **JetBrains Mono** | 92 | 90 | 85 | 85 | 93 | 93 | 88 | 88 | 85 | 45 | 30 | 50 | 66 | 66 | 35 | 35 | 76 | 76 | 25 | 25 | 217 | 217 |
| **IBM Plex Mono** | 98 | 92 | 66 | 66 | 80 | 80 | 56 | 56 | 106 | 54 | 80 | 80 | 54 | 54 | 30 | 30 | 68 | 68 | 35 | 35 | 226 | 226 |
| **Source Code Pro** | 93 | 77 | 60 | 60 | 79 | 79 | 48 | 48 | 90 | 186 | 81 | 63 | 58 | 42 | 8 | 8 | 72 | 72 | 10 | 10 | 219 | 219 |
| **Fira Code** | 100 | 100 | 74 | 74 | 84 | 84 | 46 | 46 | 120 | 84 | 60 | 96 | 50 | 50 | 18 | 18 | 30 | 30 | 4 | 4 | 212 | 212 |
| **Cascadia Code** | 82 | 82 | 66 | 66 | 68 | 68 | 37 | 37 | 78 | 48 | 48 | 62 | 55 | 55 | 34 | 34 | 62 | 62 | 10 | 10 | 221 | 221 |
| **Commit Mono** | 107 | 94 | 64 | 64 | 66 | 66 | 36 | 36 | 108 | 84 | 65 | 93 | 41 | 37 | 16 | 16 | 42 | 42 | -4 | -4 | 223 | 223 |
| **Recursive Mono Linear** | 93 | 86 | 72 | 72 | 73 | 73 | 62 | 62 | 86 | 234 | 68 | 68 | 48 | 48 | 31 | 32 | 64 | 64 | 24 | 26 | 222 | 222 |
| **Intel One Mono** | 95 | 92 | 64 | 64 | 92 | 92 | 56 | 56 | 114 | 83 | 59 | 86 | 53 | 52 | 44 | 43 | 62 | 62 | 46 | 46 | 220 | 220 |
| **DejaVu Sans Mono** | 95 | 89 | 67 | 67 | 67 | 67 | 57 | 57 | 87 | 69 | 78 | 97 | 53 | 48 | 0 | 0 | 42 | 43 | 0 | 0 | 239 | 240 |
| Roboto Mono | 85 | 80 | 60 | 60 | 69 | 69 | 52 | 53 | 99 | 59 | 99 | 59 | 45 | 44 | 23 | 19 | 72 | 63 | 36 | 23 | 242 | 215 |
| Red Hat Mono | 99 | 96 | 63 | 63 | 72 | 72 | 37 | 37 | 75 | 71 | 75 | 71 | 67 | 63 | 38 | 38 | 59 | 59 | 25 | 25 | 235 | 235 |
| Space Mono | 87 | 87 | 57 | 57 | 73 | 73 | 60 | 60 | 99 | 99 | 87 | 87 | 48 | 48 | 18 | 18 | 46 | 46 | 11 | 11 | 236 | 236 |
| Ubuntu Mono | 71 | 68 | 40 | 40 | 45 | 45 | 29 | 28 | 54 | 50 | 54 | 50 | 41 | 36 | 19 | 19 | 32 | 32 | 32 | 32 | 177 | 176 |
| Victor Mono | 86 | 74 | 73 | 72 | 72 | 71 | 55 | 54 | 114 | 61 | 117 | 63 | 45 | 45 | 25 | 24 | 48 | 47 | 21 | 21 | 228 | 228 |
| Geist Mono | 84 | 84 | 58 | 58 | 60 | 60 | 38 | 38 | 80 | 40 | 60 | 60 | 40 | 40 | 20 | 20 | 50 | 50 | 30 | 30 | 238 | 238 |
| Atkinson Hyperlegible Mono | 103 | 100 | 64 | 64 | 61 | 61 | 40 | 40 | 110 | 86 | 108 | 88 | 63 | 61 | 29 | 29 | 46 | 46 | 11 | 11 | 246 | 246 |
| Martian Mono | 113 | 102 | 78 | 78 | 93 | 93 | 58 | 58 | 145 | 82 | 130 | 97 | 76 | 72 | 30 | 30 | 73 | 73 | 23 | 23 | 258 | 258 |
| Inconsolata | 72 | 69 | 39 | 39 | 50 | 51 | 27 | 27 | 100 | 104 | 79 | 79 | 38 | 31 | 16 | 19 | 41 | 40 | 17 | 12 | 180 | 205 |
| Noto Sans Mono | 80 | 75 | 55 | 55 | 70 | 70 | 45 | 45 | 80 | 60 | 80 | 60 | 50 | 49 | 16 | 15 | 50 | 50 | 25 | 25 | 238 | 238 |
| Courier Prime | 38 | 29 | 64 | 64 | 39 | 39 | 43 | 43 | 91 | 64 | 86 | 69 | -2 | -13 | -5 | -5 | 15 | 15 | -5 | -5 | 234 | 234 |
| DM Mono | 88 | 84 | 60 | 60 | 47 | 46 | 28 | 28 | 100 | 100 | 75 | 103 | 37 | 43 | 14 | 13 | 50 | 50 | 2 | 2 | 225 | 225 |
| Sometype Mono | 89 | 83 | 52 | 52 | 75 | 75 | 47 | 47 | 54 | 54 | 31 | 31 | 54 | 51 | 15 | 15 | 66 | 66 | 9 | 9 | 215 | 215 |
| Fragment Mono | 101 | 100 | 72 | 72 | 79 | 78 | 37 | 37 | 97 | 98 | 117 | 78 | 39 | 39 | 22 | 22 | 64 | 64 | 23 | 23 | 241 | 241 |
| Azeret Mono | 81 | 76 | 50 | 51 | 66 | 65 | 32 | 30 | 77 | 80 | 72 | 70 | 50 | 50 | 21 | 19 | 26 | 24 | 17 | 15 | 263 | 263 |
| Spline Sans Mono | 96 | 90 | 62 | 62 | 67 | 67 | 42 | 42 | 100 | 54 | 57 | 62 | 40 | 32 | -4 | -4 | 43 | 43 | -4 | -4 | 219 | 219 |
| Anonymous Pro | 24 | 115 | -10 | 79 | 24 | 115 | -16 | 74 | 91 | 182 | 91 | 182 | 0 | 91 | -13 | 76 | 24 | 115 | -31 | 60 | 182 | 273 |
| Overpass Mono | 104 | 102 | 70 | 70 | 98 | 98 | 73 | 72 | 140 | 113 | 108 | 124 | 51 | 50 | 26 | 26 | 98 | 98 | 42 | 42 | 241 | 241 |
| Oxygen Mono | 96 | 85 | 67 | 67 | 68 | 68 | 60 | 60 | 107 | 81 | 67 | 88 | 49 | 44 | 12 | 12 | 73 | 73 | 32 | 36 | 226 | 227 |
| Share Tech Mono | 87 | 87 | 83 | 84 | 80 | 80 | 70 | 70 | 80 | 80 | 70 | 70 | 43 | 43 | 35 | 35 | 53 | 52 | 51 | 55 | 220 | 220 |
| PT Mono | 18 | 75 | 57 | 57 | 60 | 60 | 48 | 48 | 105 | 71 | 70 | 137 | 41 | 41 | 10 | 10 | 60 | 60 | 15 | 15 | 233 | 233 |
| Cousine | 87 | 88 | 64 | 64 | 79 | 80 | 50 | 50 | 70 | 51 | 65 | 55 | 48 | 51 | 10 | 10 | 63 | 64 | 0 | 0 | 242 | 243 |
| Go Mono | 35 | 32 | 54 | 54 | 30 | 30 | 30 | 30 | 72 | 60 | 44 | 56 | 13 | 14 | 11 | 11 | 12 | 12 | 11 | 11 | 218 | 218 |
| Iosevka | 64 | 64 | 56 | 56 | 64 | 64 | 56 | 56 | 75 | 75 | 75 | 75 | 51 | 51 | 35 | 35 | 51 | 51 | 35 | 35 | 172 | 172 |
| JuliaMono | 75 | 75 | 71 | 71 | 95 | 95 | 32 | 34 | 92 | 92 | 60 | 34 | 45 | 45 | 38 | 38 | 61 | 61 | 52 | 53 | 208 | 208 |
| Fira Mono (dup) | 100 | 99 | 73 | 73 | 83 | 83 | 47 | 47 | 121 | 85 | 60 | 97 | 51 | 51 | 18 | 18 | 30 | 30 | 5 | 5 | 211 | 213 |
| Cascadia Mono (dup) | 82 | 82 | 66 | 66 | 68 | 68 | 37 | 37 | 78 | 48 | 48 | 62 | 55 | 55 | 34 | 34 | 62 | 62 | 10 | 10 | 221 | 221 |
| Liberation Mono (dup) | 87 | 88 | 64 | 64 | 79 | 80 | 50 | 50 | 70 | 51 | 130 | 55 | 48 | 51 | 10 | 10 | 63 | 64 | 0 | 0 | 242 | 243 |
| Hack (dup) | 95 | 89 | 67 | 67 | 67 | 67 | 57 | 57 | 131 | 69 | 88 | 87 | 53 | 48 | 0 | 0 | 42 | 43 | 0 | 0 | 220 | 224 |
| Monaspace Neon (extra) | 94 | 94 | 60 | 60 | 86 | 86 | 48 | 48 | 80 | 80 | 80 | 80 | 76 | 75 | 13 | 13 | 71 | 71 | 16 | 16 | 218 | 218 |
| 0xProto (extra) | 87 | 89 | 65 | 65 | 80 | 80 | 40 | 40 | 85 | 87 | 93 | 111 | 45 | 45 | 41 | 41 | 33 | 33 | 30 | 30 | 227 | 227 |
| mononoki (extra) | 83 | 83 | 83 | 83 | 66 | 66 | 83 | 83 | 83 | 83 | 86 | 77 | 50 | 50 | 30 | 29 | 30 | 29 | 30 | 29 | 207 | 208 |
| B612 Mono (extra) | 106 | 105 | 72 | 78 | 80 | 82 | 50 | 50 | 100 | 74 | 94 | 100 | 43 | 39 | 50 | 50 | 60 | 74 | 19 | 20 | 68 | 418 |

| font | n counter | o counter | m counter 1 | m counter 2 | H counter | n counter / stem | n-n gap | gap / counter | n w/adv | o w/adv | H w/adv | O w/adv | 0 w / O w |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **JetBrains Mono** | 238 | 250 | 115 | 115 | 234 | 2.64 | 182 | 0.765 | 0.697 | 0.717 | 0.690 | 0.707 | 1.038 |
| **IBM Plex Mono** | 250 | 298 | 135 | 135 | 272 | 3.12 | 190 | 0.760 | 0.683 | 0.780 | 0.733 | 0.813 | 1.000 |
| **Source Code Pro** | 266 | 310 | 130 | 130 | 274 | 3.24 | 170 | 0.639 | 0.717 | 0.800 | 0.737 | 0.840 | 0.909 |
| **Fira Code** | 232 | 273 | 132 | 132 | 260 | 2.76 | 200 | 0.862 | 0.667 | 0.755 | 0.722 | 0.845 | 0.889 |
| **Cascadia Code** | 215 | 238 | 91 | 91 | 246 | 2.08 | 164 | 0.763 | 0.720 | 0.773 | 0.767 | 0.873 | 0.924 |
| **Commit Mono** | 231 | 302 | 138 | 138 | 294 | 2.75 | 201 | 0.870 | 0.665 | 0.787 | 0.780 | 0.880 | 0.901 |
| **Recursive Mono Linear** | 237 | 274 | 130 | 130 | 268 | 2.58 | 179 | 0.755 | 0.702 | 0.760 | 0.757 | 0.793 | 0.971 |
| **Intel One Mono** | 255 | 312 | 139 | 138 | 256 | 2.97 | 187 | 0.733 | 0.695 | 0.791 | 0.700 | 0.818 | 0.956 |
| **DejaVu Sans Mono** | 238 | 278 | 127 | 128 | 270 | 2.65 | 184 | 0.774 | 0.694 | 0.778 | 0.778 | 0.810 | 0.968 |
| Roboto Mono | 254 | 300 | 126 | 126 | 292 | 2.82 | 165 | 0.649 | 0.725 | 0.801 | 0.770 | 0.826 | 0.929 |
| Red Hat Mono | 259 | 330 | 135 | 133 | 302 | 3.55 | 195 | 0.753 | 0.675 | 0.790 | 0.760 | 0.877 | 0.981 |
| Space Mono | 282 | 338 | 141 | 141 | 298 | 3.62 | 174 | 0.617 | 0.716 | 0.814 | 0.761 | 0.804 | 1.000 |
| Ubuntu Mono | 196 | 250 | 99 | 99 | 246 | 2.36 | 139 | 0.709 | 0.722 | 0.840 | 0.820 | 0.886 | 0.921 |
| Victor Mono | 290 | 305 | 143 | 142 | 307 | 3.87 | 160 | 0.552 | 0.733 | 0.758 | 0.762 | 0.818 | 1.000 |
| Geist Mono | 264 | 308 | 134 | 134 | 308 | 3.14 | 168 | 0.636 | 0.720 | 0.807 | 0.800 | 0.873 | 0.954 |
| Atkinson Hyperlegible Mono | 258 | 330 | 140 | 140 | 334 | 3.04 | 203 | 0.787 | 0.679 | 0.797 | 0.807 | 0.873 | 0.953 |
| Martian Mono | 265 | 326 | 119 | 119 | 286 | 2.41 | 215 | 0.811 | 0.693 | 0.777 | 0.734 | 0.834 | 1.000 |
| Inconsolata | 219 | 270 | 116 | 116 | 243 | 3.13 | 141 | 0.644 | 0.718 | 0.844 | 0.798 | 0.892 | 0.866 |
| Noto Sans Mono | 265 | 310 | 131 | 130 | 280 | 2.94 | 155 | 0.585 | 0.742 | 0.817 | 0.767 | 0.850 | 0.941 |
| Courier Prime | 235 | 316 | 131 | 131 | 243 | 3.22 | 66 | 0.282 | 0.889 | 0.785 | 0.870 | 0.857 | 0.810 |
| DM Mono | 260 | 308 | 136 | 136 | 339 | 3.10 | 172 | 0.661 | 0.713 | 0.800 | 0.845 | 0.907 | 0.982 |
| Sometype Mono | 264 | 328 | 134 | 134 | 282 | 3.67 | 172 | 0.651 | 0.703 | 0.821 | 0.741 | 0.838 | 0.975 |
| Fragment Mono | 251 | 300 | 147 | 147 | 275 | 3.02 | 201 | 0.801 | 0.675 | 0.767 | 0.746 | 0.880 | 0.853 |
| Azeret Mono | 291 | 346 | 136 | 136 | 307 | 2.88 | 157 | 0.539 | 0.758 | 0.845 | 0.798 | 0.905 | 0.915 |
| Spline Sans Mono | 228 | 286 | 140 | 139 | 279 | 2.46 | 186 | 0.812 | 0.691 | 0.793 | 0.777 | 0.860 | 0.977 |
| Anonymous Pro | 273 | 343 | 127 | 127 | 273 | 4.08 | 139 | 0.508 | 0.746 | 0.873 | 0.746 | 0.894 | 1.000 |
| Overpass Mono | 248 | 309 | 138 | 136 | 254 | 3.04 | 206 | 0.832 | 0.666 | 0.773 | 0.680 | 0.764 | 1.034 |
| Oxygen Mono | 241 | 286 | 138 | 132 | 281 | 2.71 | 181 | 0.751 | 0.698 | 0.775 | 0.772 | 0.799 | 1.000 |
| Share Tech Mono | 196 | 203 | 107 | 107 | 206 | 2.31 | 174 | 0.888 | 0.678 | 0.691 | 0.704 | 0.741 | 0.890 |
| PT Mono | 277 | 321 | 145 | 145 | 314 | 3.60 | 93 | 0.336 | 0.845 | 0.810 | 0.800 | 0.840 | 0.970 |
| Cousine | 246 | 288 | 126 | 126 | 255 | 2.79 | 175 | 0.714 | 0.708 | 0.787 | 0.736 | 0.833 | 0.956 |
| Go Mono | 223 | 284 | 121 | 120 | 239 | 2.30 | 67 | 0.303 | 0.888 | 0.819 | 0.900 | 0.900 | 0.937 |
| Iosevka | 216 | 232 | 91 | 91 | 216 | 2.77 | 128 | 0.593 | 0.744 | 0.776 | 0.744 | 0.776 | 1.000 |
| JuliaMono | 266 | 282 | 114 | 120 | 236 | 3.04 | 150 | 0.564 | 0.750 | 0.763 | 0.683 | 0.890 | 0.899 |
| Fira Mono (dup) | 233 | 272 | 133 | 133 | 260 | 2.77 | 199 | 0.854 | 0.668 | 0.757 | 0.723 | 0.843 | 0.889 |
| Cascadia Mono (dup) | 215 | 238 | 91 | 91 | 246 | 2.08 | 164 | 0.763 | 0.720 | 0.773 | 0.767 | 0.873 | 0.924 |
| Liberation Mono (dup) | 246 | 288 | 126 | 126 | 255 | 2.79 | 175 | 0.714 | 0.708 | 0.787 | 0.736 | 0.833 | 0.956 |
| Hack (dup) | 238 | 278 | 127 | 128 | 270 | 2.65 | 184 | 0.774 | 0.694 | 0.778 | 0.778 | 0.810 | 0.968 |
| Monaspace Neon (extra) | 242 | 306 | 106 | 106 | 256 | 2.56 | 189 | 0.781 | 0.695 | 0.808 | 0.724 | 0.844 | 1.000 |
| 0xProto (extra) | 249 | 300 | 130 | 130 | 264 | 2.59 | 176 | 0.707 | 0.716 | 0.790 | 0.742 | 0.871 | 0.944 |
| mononoki (extra) | 230 | 230 | 106 | 106 | 263 | 2.77 | 166 | 0.723 | 0.704 | 0.704 | 0.763 | 0.704 | 1.148 |
| B612 Mono (extra) | 260 | 310 | 150 | 151 | 284 | 2.88 | 210 | 0.811 | 0.676 | 0.770 | 0.751 | 0.846 | 0.927 |

Observations. Negative sidebearings appear only on `w`, `W`, `m` and in the widest designs. The zero is narrower than the capital O in 25 of 34 (median ratio 0.956); JetBrains Mono is the exception among the callouts with a zero 3.8 percent wider than its O.

### 4.6 Squareness

| font | o outer f | o outer n | o inner f | o inner n | O outer f | O outer n | O inner f | 0 outer f | o w/h | O w/h |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **JetBrains Mono** | 0.770 | 2.66 | 0.795 | 3.03 | 0.806 | 3.21 | 0.835 | 0.799 | 0.760 | 0.565 |
| **IBM Plex Mono** | 0.730 | 2.21 | 0.767 | 2.62 | 0.750 | 2.41 | 0.775 | 0.750 | 0.867 | 0.676 |
| **Source Code Pro** | 0.719 | 2.10 | 0.725 | 2.16 | 0.729 | 2.19 | 0.731 | 0.737 | 0.941 | 0.741 |
| **Fira Code** | 0.735 | 2.25 | 0.752 | 2.43 | 0.736 | 2.26 | 0.755 | 0.744 | 0.825 | 0.713 |
| **Cascadia Code** | 0.738 | 2.28 | 0.740 | 2.30 | 0.750 | 2.41 | 0.750 | 0.750 | 0.844 | 0.718 |
| **Commit Mono** | 0.717 | 2.09 | 0.721 | 2.12 | 0.721 | 2.11 | 0.727 | 0.735 | 0.843 | 0.733 |
| **Recursive Mono Linear** | 0.751 | 2.42 | 0.767 | 2.61 | 0.788 | 2.91 | 0.815 | 0.768 | 0.823 | 0.643 |
| **Intel One Mono** | 0.722 | 2.13 | 0.727 | 2.17 | 0.737 | 2.27 | 0.745 | 0.738 | 0.982 | 0.733 |
| **DejaVu Sans Mono** | 0.743 | 2.34 | 0.747 | 2.38 | 0.753 | 2.44 | 0.768 | 0.747 | 0.816 | 0.645 |
| Roboto Mono | 0.725 | 2.16 | 0.730 | 2.20 | 0.738 | 2.28 | 0.751 | 0.771 | 0.877 | 0.678 |
| Red Hat Mono | 0.712 | 2.04 | 0.716 | 2.07 | 0.721 | 2.12 | 0.724 | 0.725 | 0.937 | 0.729 |
| Space Mono | 0.722 | 2.13 | 0.723 | 2.14 | 0.768 | 2.63 | 0.777 | 0.768 | 0.950 | 0.676 |
| Ubuntu Mono | 0.722 | 2.13 | 0.731 | 2.21 | 0.740 | 2.30 | 0.748 | 0.740 | 0.864 | 0.686 |
| Victor Mono | 0.780 | 2.79 | 0.787 | 2.89 | 0.792 | 2.97 | 0.799 | 0.716 | 0.704 | 0.593 |
| Geist Mono | 0.728 | 2.18 | 0.735 | 2.25 | 0.741 | 2.31 | 0.742 | 0.732 | 0.874 | 0.706 |
| Atkinson Hyperlegible Mono | 0.724 | 2.15 | 0.728 | 2.18 | 0.730 | 2.20 | 0.731 | 0.738 | 0.971 | 0.798 |
| Martian Mono | 0.730 | 2.20 | 0.737 | 2.27 | 0.750 | 2.41 | 0.758 | 0.750 | 0.861 | 0.702 |
| Inconsolata | 0.719 | 2.10 | 0.718 | 2.09 | 0.739 | 2.29 | 0.735 | 0.739 | 0.888 | 0.699 |
| Noto Sans Mono | 0.734 | 2.24 | 0.742 | 2.32 | 0.744 | 2.34 | 0.756 | 0.751 | 0.881 | 0.693 |
| Courier Prime | 0.717 | 2.09 | 0.725 | 2.15 | 0.725 | 2.16 | 0.729 | 0.727 | 0.996 | 0.855 |
| DM Mono | 0.723 | 2.14 | 0.735 | 2.25 | 0.731 | 2.21 | 0.732 | 0.728 | 0.923 | 0.751 |
| Sometype Mono | 0.725 | 2.16 | 0.733 | 2.23 | 0.747 | 2.38 | 0.750 | 0.743 | 0.964 | 0.721 |
| Fragment Mono | 0.736 | 2.26 | 0.733 | 2.23 | 0.737 | 2.27 | 0.735 | 0.745 | 0.850 | 0.742 |
| Azeret Mono | 0.733 | 2.23 | 0.733 | 2.23 | 0.728 | 2.18 | 0.727 | 0.733 | 0.956 | 0.814 |
| Spline Sans Mono | 0.728 | 2.18 | 0.736 | 2.26 | 0.736 | 2.26 | 0.747 | 0.759 | 0.844 | 0.682 |
| Anonymous Pro | 0.724 | 2.14 | 0.725 | 2.15 | 0.735 | 2.25 | 0.737 | 0.735 | 0.999 | 0.741 |
| Overpass Mono | 0.731 | 2.21 | 0.739 | 2.29 | 0.732 | 2.22 | 0.732 | 0.736 | 0.891 | 0.650 |
| Oxygen Mono | 0.732 | 2.22 | 0.745 | 2.35 | 0.735 | 2.25 | 0.731 | 0.735 | 0.825 | 0.637 |
| Share Tech Mono | 0.818 | 3.44 | 0.869 | 4.94 | 0.836 | 3.88 | 0.880 | 0.829 | 0.746 | 0.571 |
| PT Mono | 0.735 | 2.25 | 0.739 | 2.29 | 0.750 | 2.41 | 0.753 | 0.749 | 0.927 | 0.696 |
| Cousine | 0.745 | 2.36 | 0.754 | 2.46 | 0.744 | 2.34 | 0.750 | 0.750 | 0.862 | 0.737 |
| Go Mono | 0.733 | 2.23 | 0.750 | 2.41 | 0.721 | 2.12 | 0.740 | 0.732 | 0.887 | 0.712 |
| Iosevka | 0.769 | 2.64 | 0.783 | 2.84 | 0.812 | 3.32 | 0.835 | 0.809 | 0.724 | 0.517 |
| JuliaMono | 0.731 | 2.21 | 0.731 | 2.22 | 0.732 | 2.22 | 0.717 | 0.779 | 0.809 | 0.715 |
| Fira Mono (dup) | 0.734 | 2.24 | 0.753 | 2.45 | 0.735 | 2.25 | 0.755 | 0.744 | 0.827 | 0.712 |
| Cascadia Mono (dup) | 0.738 | 2.28 | 0.740 | 2.30 | 0.750 | 2.41 | 0.750 | 0.750 | 0.844 | 0.718 |
| Liberation Mono (dup) | 0.745 | 2.36 | 0.754 | 2.46 | 0.744 | 2.34 | 0.750 | 0.750 | 0.862 | 0.737 |
| Hack (dup) | 0.743 | 2.33 | 0.741 | 2.32 | 0.753 | 2.44 | 0.767 | 0.747 | 0.816 | 0.645 |
| Monaspace Neon (extra) | 0.729 | 2.19 | 0.739 | 2.29 | 0.743 | 2.33 | 0.757 | 0.744 | 0.932 | 0.694 |
| 0xProto (extra) | 0.734 | 2.24 | 0.744 | 2.34 | 0.743 | 2.33 | 0.755 | 0.754 | 0.842 | 0.728 |
| mononoki (extra) | 0.731 | 2.22 | 0.730 | 2.21 | 0.778 | 2.76 | 0.785 | 0.732 | 0.773 | 0.562 |
| B612 Mono (extra) | 0.720 | 2.11 | 0.728 | 2.18 | 0.728 | 2.18 | 0.752 | 0.720 | 0.883 | 0.717 |

f is the diagonal crossing as a fraction of the half-diagonal (ellipse 0.7071, rectangle 1.0); n is the equivalent superellipse exponent. Squarest o in the core set: Share Tech Mono 0.818, Victor Mono 0.780, JetBrains Mono 0.770, Iosevka 0.769, Recursive Mono Linear 0.751, Cousine 0.745. Roundest: Source Code Pro 0.719, Courier Prime 0.717, Commit Mono 0.717, Red Hat Mono 0.712. The inner contour is squarer than the outer one in 32 of 34, and the capital O is squarer than the lowercase o in 31: the narrower the bowl relative to its height, the more the designer squares it.

### 4.7 Punctuation

| font | period w | period h | period fill | comma top | comma bottom | colon lower y | colon upper y | colon top - x | colon centre - axis | hyphen w | hyphen thick | hyphen y | hyphen y/x | U+2212 w | U+2212 y | underscore top | underscore bottom | underscore w | underscore w/adv |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **JetBrains Mono** | 166 | 166 | 0.812 | 151 | -160 | 65 | 485 | 10 | -55 | 320 | 80 | 330.0 | 0.600 | 320 | 330.0 | -25 | -100 | 480 | 0.800 |
| **IBM Plex Mono** | 148 | 138 | 0.853 | 136 | -141 | 60 | 456 | 9 | -47 | 290 | 84 | 304.0 | 0.589 | 476 | 305.0 | -95 | -169 | 480 | 0.800 |
| **Source Code Pro** | 162 | 169 | 0.796 | 155 | -213 | 72 | 430 | 29 | -80 | 430 | 62 | 330.0 | 0.679 | 430 | 330.0 | -69 | -140 | 480 | 0.800 |
| **Fira Code** | 176 | 176 | 0.792 | 164 | -180 | 70 | 430 | -16 | -62 | 401 | 73 | 313.0 | 0.595 | 369 | 312.5 | -108 | -182 | 500 | 0.833 |
| **Cascadia Code** | 144 | 144 | 0.789 | 124 | -213 | 62 | 455 | 10 | -87 | 488 | 91 | 346.2 | 0.669 | 488 | 346.2 | 0 | -91 | 488 | 0.833 |
| **Commit Mono** | 154 | 154 | 0.788 | 121 | -158 | 69 | 471 | 8 | -40 | 388 | 76 | 310.0 | 0.574 | 448 | 310.0 | -46 | -122 | 460 | 0.767 |
| **Recursive Mono Linear** | 156 | 153 | 0.998 | 171 | -200 | 70 | 462 | 7 | -34 | 362 | 89 | 299.5 | 0.563 | 462 | 300.5 | -79 | -167 | 470 | 0.783 |
| **Intel One Mono** | 174 | 162 | 0.825 | 132 | -152 | 63 | 400 | 13 | -93 | 374 | 83 | 327.5 | 0.704 | 474 | 327.5 | -26 | -106 | 458 | 0.746 |
| **DejaVu Sans Mono** | 123 | 149 | 1.000 | 148 | -140 | 74 | 445 | -28 | -54 | 254 | 80 | 273.9 | 0.501 | 516 | 313.5 | -197 | -236 | 602 | 1.000 |
| Roboto Mono | 143 | 138 | 0.811 | 107 | -164 | 60 | 487 | 28 | -47 | 374 | 74 | 311.0 | 0.589 | 408 | 354.7 | 0 | -74 | 448 | 0.746 |
| Red Hat Mono | 130 | 130 | 0.793 | 74 | -157 | 56 | 453 | 30 | -94 | 332 | 60 | 280.0 | 0.574 | 446 | 348.0 | -80 | -137 | 460 | 0.767 |
| Space Mono | 140 | 140 | 0.784 | 126 | -120 | 56 | 440 | 14 | -102 | 300 | 72 | 260.0 | 0.524 | 418 | 350.0 | -48 | -120 | 466 | 0.761 |
| Ubuntu Mono | 147 | 153 | 0.795 | 139 | -144 | 64 | 388 | 0 | -32 | 220 | 78 | 254.0 | 0.547 | 409 | 263.0 | -95 | -165 | 484 | 0.968 |
| Victor Mono | 144 | 135 | 0.868 | 121 | -196 | 54 | 562 | 12 | -92 | 385 | 69 | 400.5 | 0.648 | 555 | 400.5 | -113 | -182 | 565 | 0.942 |
| Geist Mono | 124 | 122 | 1.000 | 122 | -162 | 61 | 447 | -22 | -39 | 360 | 79 | 291.5 | 0.550 | 440 | 295.0 | 0 | -78 | 440 | 0.733 |
| Atkinson Hyperlegible Mono | 140 | 140 | 0.786 | 128 | -144 | 58 | 445 | 19 | 2 | 290 | 79 | 248.5 | 0.501 | 502 | 249.5 | 0 | -77 | 636 | 1.006 |
| Martian Mono | 184 | 191 | 0.822 | 183 | -180 | 88 | 512 | 8 | -50 | 566 | 100 | 350.0 | 0.583 | 566 | 350.0 | -50 | -150 | 566 | 0.809 |
| Inconsolata | 115 | 114 | 0.783 | 103 | -168 | 46 | 366 | -34 | -105 | 280 | 67 | 314.5 | 0.688 | 411 | 321.5 | -19 | -80 | 431 | 0.862 |
| Noto Sans Mono | 124 | 136 | 0.825 | 129 | -140 | 58 | 478 | 10 | -89 | 300 | 80 | 270.0 | 0.504 | 460 | 348.0 | -74 | -154 | 600 | 1.000 |
| Courier Prime | 132 | 151 | 0.939 | 144 | -144 | 71 | 380 | 5 | -59 | 434 | 66 | 284.2 | 0.630 | 434 | 284.2 | -123 | -190 | 627 | 1.046 |
| DM Mono | 150 | 145 | 0.790 | 147 | -122 | 70 | 466 | 42 | -82 | 330 | 72 | 350.0 | 0.706 | 450 | 350.0 | 0 | -77 | 450 | 0.750 |
| Sometype Mono | 150 | 150 | 0.786 | 138 | -189 | 63 | 407 | 12 | -40 | 400 | 66 | 275.0 | 0.585 | 480 | 275.0 | -72 | -138 | 580 | 1.000 |
| Fragment Mono | 136 | 136 | 1.000 | 136 | -165 | 68 | 456 | 0 | -60 | 378 | 72 | 322.0 | 0.615 | 504 | 322.0 | -146 | -218 | 618 | 1.000 |
| Azeret Mono | 124 | 124 | 1.000 | 123 | -177 | 62 | 431 | -57 | -61 | 306 | 89 | 309.5 | 0.563 | 516 | 308.5 | 0 | -88 | 483 | 0.743 |
| Spline Sans Mono | 162 | 173 | 0.802 | 153 | -274 | 72 | 440 | -18 | -113 | 381 | 79 | 358.5 | 0.657 | 448 | 375.0 | -26 | -100 | 604 | 1.007 |
| Anonymous Pro | 91 | 91 | 1.000 | 91 | -182 | 45 | 409 | 0 | -6 | 455 | 57 | 233.6 | 0.513 | 455 | 233.6 | -34 | -91 | 455 | 0.834 |
| Overpass Mono | 134 | 134 | 0.785 | 118 | -174 | 53 | 417 | -28 | -111 | 470 | 78 | 297.8 | 0.583 | 470 | 342.5 | -96 | -177 | 618 | 1.004 |
| Oxygen Mono | 147 | 147 | 1.000 | 140 | -157 | 144 | 478 | 16 | -58 | 327 | 76 | 366.0 | 0.683 | 566 | 299.1 | -77 | -144 | 523 | 0.872 |
| Share Tech Mono | 100 | 100 | 1.000 | 100 | -140 | 50 | 450 | 0 | -74 | 325 | 75 | 312.5 | 0.625 | 380 | 312.5 | -95 | -170 | 504 | 0.933 |
| PT Mono | 134 | 134 | 0.812 | 122 | -149 | 55 | 448 | 15 | -81 | 342 | 74 | 288.0 | 0.576 | 464 | 338.0 | -135 | -205 | 488 | 0.813 |
| Cousine | 115 | 146 | 1.000 | 146 | -177 | 73 | 455 | 0 | -66 | 273 | 78 | 265.6 | 0.503 | 486 | 332.5 | -60 | -107 | 604 | 1.007 |
| Go Mono | 164 | 164 | 1.000 | 164 | -193 | 82 | 460 | 12 | -30 | 503 | 72 | 301.3 | 0.568 | 503 | 301.3 | 0 | -72 | 600 | 1.000 |
| Iosevka | 156 | 156 | 0.820 | 148 | -215 | 70 | 450 | 8 | -80 | 372 | 70 | 340.0 | 0.654 | 372 | 340.0 | 0 | -70 | 372 | 0.744 |
| JuliaMono | 184 | 184 | 0.833 | 173 | -195 | 96 | 462 | 4 | 4 | 412 | 100 | 275.0 | 0.500 | 471 | 275.0 | 66 | -20 | 486 | 0.810 |
| Fira Mono (dup) | 176 | 176 | 0.794 | 165 | -179 | 70 | 430 | -16 | -62 | 350 | 72 | 313.0 | 0.594 | 368 | 312.5 | -108 | -182 | 500 | 0.833 |
| Cascadia Mono (dup) | 144 | 144 | 0.789 | 124 | -213 | 62 | 455 | 10 | -87 | 488 | 91 | 346.2 | 0.669 | 488 | 346.2 | 0 | -91 | 488 | 0.833 |
| Liberation Mono (dup) | 115 | 146 | 1.000 | 146 | -177 | 73 | 455 | 0 | -66 | 273 | 78 | 265.6 | 0.503 | 486 | 332.5 | -60 | -107 | 604 | 1.007 |
| Hack (dup) | 158 | 165 | 0.798 | 170 | -189 | 112 | 461 | -3 | -27 | 401 | 80 | 293.5 | 0.537 | 516 | 313.5 | -93 | -151 | 510 | 0.847 |
| Monaspace Neon (extra) | 185 | 180 | 0.803 | 162 | -222 | 75 | 464 | 40 | -58 | 320 | 82 | 327.5 | 0.638 | 440 | 327.5 | -115 | -180 | 530 | 0.855 |
| 0xProto (extra) | 166 | 166 | 0.789 | 151 | -193 | 75 | 475 | 0 | -31 | 410 | 86 | 307.0 | 0.558 | 480 | 302.5 | 0 | -86 | 486 | 0.784 |
| mononoki (extra) | 146 | 137 | 0.980 | 137 | -241 | 68 | 420 | 0 | -0 | 462 | 75 | 244.6 | 0.501 | 462 | 244.6 | 0 | -75 | 462 | 0.823 |
| B612 Mono (extra) | 164 | 166 | 0.784 | 136 | -154 | 66 | 323 | -162 | -106 | 250 | 78 | 261.2 | 0.466 | 450 | 311.2 | -150 | -228 | 550 | 0.846 |

"period fill" is the area of the dot over the area of its bbox: 0.785 for a circle, 1.0 for a square. The period is round in 23 of 34 and square or nearly so in 11. Its diameter is 1.72 stems at the median. The colon's upper dot ends near the x-height (median 8 above it), so the pair is centred 61 below the math axis at the median; only Atkinson Hyperlegible Mono, Anonymous Pro, JuliaMono centre the colon on the operators (within 12 units). The underscore spans the full advance (ratio 0.99 or more) in 10 of 34, so consecutive underscores join; in the rest they leave gaps. U+2212 MINUS has the width of the plus in 23 of 34; the ASCII hyphen-minus has the width of the plus in only 8.

### 4.8 Operators and the math axis

| font | + y | = y | < y | > y | axis | spread | axis/x | axis/cap | axis - cell centre | - y - axis | * y - axis | + w | + h | + stroke | = w | = bar | = gap | < w | < h | * w | * h |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **JetBrains Mono** | 330.0 | 330.0 | 330.0 | 330.0 | 330.0 | 0.0 | 0.600 | 0.452 | -30 | 0.0 | 22 | 470 | 470 | 80.0 | 430 | 80.0 | 160 | 430 | 530 | 530 | 516 |
| **IBM Plex Mono** | 305.0 | 306.0 | 305.0 | 305.0 | 305.2 | 1.0 | 0.592 | 0.437 | -70 | -1.2 | 15 | 476 | 486 | 68.0 | 476 | 68.0 | 132 | 430 | 578 | 514 | 496 |
| **Source Code Pro** | 330.0 | 330.0 | 332.0 | 332.0 | 331.0 | 2.0 | 0.681 | 0.505 | -24 | -1.0 | 2 | 430 | 452 | 62.0 | 430 | 62.0 | 152 | 373 | 568 | 432 | 445 |
| **Fira Code** | 311.5 | 310.8 | 313.5 | 313.5 | 312.3 | 2.7 | 0.593 | 0.454 | -22 | 0.7 | 26 | 469 | 468 | 70.5 | 389 | 73.0 | 117 | 425 | 561 | 503 | 480 |
| **Cascadia Code** | 346.2 | 346.2 | 346.2 | 346.2 | 346.2 | 0.0 | 0.669 | 0.499 | -0 | 0.0 | 4 | 488 | 507 | 90.8 | 488 | 90.8 | 153 | 468 | 483 | 477 | 448 |
| **Commit Mono** | 310.0 | 310.0 | 310.0 | 310.0 | 310.0 | 0.0 | 0.574 | 0.443 | -40 | 0.0 | -6 | 468 | 468 | 76.0 | 428 | 74.0 | 118 | 404 | 508 | 480 | 457 |
| **Recursive Mono Linear** | 300.5 | 299.5 | 299.5 | 299.5 | 299.8 | 1.0 | 0.564 | 0.428 | -50 | -0.3 | 1 | 462 | 461 | 90.0 | 462 | 89.0 | 166 | 440 | 567 | 467 | 468 |
| **Intel One Mono** | 327.0 | 327.5 | 321.0 | 321.0 | 324.1 | 6.5 | 0.697 | 0.495 | -76 | 3.4 | 71 | 474 | 480 | 71.0 | 428 | 72.0 | 124 | 470 | 484 | 495 | 470 |
| **DejaVu Sans Mono** | 313.5 | 313.0 | 313.5 | 313.5 | 313.4 | 0.5 | 0.573 | 0.430 | -33 | -39.5 | 201 | 516 | 517 | 83.0 | 516 | 84.0 | 115 | 516 | 489 | 440 | 456 |
| Roboto Mono | 330.1 | 318.8 | 316.2 | 316.7 | 320.5 | 13.9 | 0.607 | 0.451 | -68 | -9.5 | 150 | 487 | 518 | 89.8 | 436 | 78.1 | 124 | 414 | 441 | 469 | 480 |
| Red Hat Mono | 348.0 | 348.0 | 348.5 | 348.5 | 348.2 | 0.5 | 0.714 | 0.497 | -8 | -68.2 | 147 | 446 | 472 | 60.0 | 446 | 60.0 | 104 | 404 | 591 | 380 | 409 |
| Space Mono | 350.0 | 350.0 | 350.0 | 350.0 | 350.0 | 0.0 | 0.706 | 0.500 | -30 | -90.0 | 0 | 418 | 418 | 72.0 | 418 | 72.0 | 72 | 418 | 440 | 496 | 496 |
| Ubuntu Mono | 262.5 | 262.5 | 254.5 | 254.5 | 258.5 | 8.0 | 0.557 | 0.418 | -72 | -4.5 | 176 | 409 | 439 | 70.0 | 409 | 71.0 | 119 | 409 | 399 | 386 | 369 |
| Victor Mono | 400.5 | 400.5 | 400.5 | 400.5 | 400.5 | 0.0 | 0.648 | 0.501 | -24 | 0.0 | 0 | 555 | 555 | 69.0 | 555 | 69.0 | 171 | 468 | 733 | 506 | 552 |
| Geist Mono | 295.0 | 299.5 | 289.0 | 289.0 | 293.1 | 10.5 | 0.553 | 0.413 | -62 | -1.6 | 204 | 478 | 478 | 78.0 | 440 | 78.0 | 129 | 456 | 512 | 440 | 426 |
| Atkinson Hyperlegible Mono | 248.0 | 251.0 | 248.5 | 248.5 | 249.0 | 3.0 | 0.502 | 0.373 | -85 | -0.5 | 248 | 502 | 496 | 74.0 | 502 | 74.0 | 107 | 472 | 491 | 357 | 339 |
| Martian Mono | 350.0 | 350.0 | 350.0 | 350.0 | 350.0 | 0.0 | 0.583 | 0.438 | -50 | 0.0 | 2 | 566 | 566 | 100.0 | 520 | 100.0 | 174 | 474 | 616 | 564 | 537 |
| Inconsolata | 313.5 | 316.0 | 307.0 | 307.0 | 310.9 | 9.0 | 0.680 | 0.499 | -24 | 3.6 | 19 | 411 | 419 | 61.0 | 411 | 61.0 | 146 | 426 | 520 | 417 | 413 |
| Noto Sans Mono | 353.0 | 352.0 | 362.0 | 362.0 | 357.2 | 10.0 | 0.666 | 0.500 | -31 | -87.2 | 183 | 440 | 464 | 71.0 | 460 | 80.0 | 110 | 420 | 492 | 423 | 412 |
| Courier Prime | 284.2 | 284.2 | 284.7 | 284.7 | 284.4 | 0.5 | 0.630 | 0.491 | 65 | -0.2 | 107 | 434 | 434 | 66.4 | 434 | 66.4 | 129 | 453 | 449 | 413 | 398 |
| DM Mono | 350.0 | 350.0 | 349.0 | 349.0 | 349.5 | 1.0 | 0.705 | 0.499 | 8 | 0.5 | 0 | 450 | 450 | 76.0 | 450 | 76.0 | 170 | 380 | 538 | 472 | 498 |
| Sometype Mono | 275.0 | 275.0 | 275.0 | 275.0 | 275.0 | 0.0 | 0.585 | 0.423 | -50 | 0.0 | 0 | 480 | 480 | 66.0 | 460 | 66.0 | 144 | 410 | 550 | 472 | 500 |
| Fragment Mono | 322.0 | 323.0 | 322.5 | 322.5 | 322.5 | 1.0 | 0.616 | 0.461 | -28 | -0.5 | 48 | 484 | 484 | 70.0 | 464 | 70.0 | 182 | 438 | 563 | 536 | 511 |
| Azeret Mono | 307.0 | 307.0 | 308.5 | 308.5 | 307.8 | 1.5 | 0.560 | 0.441 | -46 | 1.7 | 227 | 506 | 506 | 89.0 | 516 | 89.0 | 126 | 515 | 477 | 385 | 351 |
| Spline Sans Mono | 374.2 | 370.8 | 365.8 | 365.8 | 369.1 | 8.4 | 0.677 | 0.508 | 6 | -10.6 | 105 | 489 | 514 | 85.0 | 470 | 84.5 | 146 | 405 | 568 | 532 | 506 |
| Anonymous Pro | 233.6 | 233.6 | 233.4 | 233.4 | 233.5 | 0.2 | 0.513 | 0.366 | -84 | 0.1 | -6 | 455 | 455 | 57.1 | 455 | 57.1 | 158 | 288 | 500 | 421 | 455 |
| Overpass Mono | 343.0 | 342.2 | 349.8 | 349.8 | 346.2 | 7.6 | 0.677 | 0.495 | 96 | -48.4 | -4 | 470 | 470 | 79.0 | 470 | 79.5 | 136 | 470 | 468 | 460 | 444 |
| Oxygen Mono | 366.9 | 367.4 | 368.9 | 374.5 | 369.4 | 7.6 | 0.690 | 0.507 | 42 | -3.4 | 21 | 566 | 522 | 73.7 | 567 | 72.3 | 143 | 501 | 552 | 545 | 518 |
| Share Tech Mono | 313.0 | 312.5 | 334.5 | 334.5 | 323.6 | 22.0 | 0.647 | 0.462 | 2 | -11.1 | 207 | 381 | 390 | 75.0 | 380 | 75.0 | 125 | 380 | 459 | 400 | 382 |
| PT Mono | 338.0 | 338.5 | 327.0 | 327.0 | 332.6 | 11.5 | 0.665 | 0.475 | 8 | -44.6 | 154 | 504 | 514 | 72.0 | 464 | 72.0 | 93 | 510 | 588 | 478 | 456 |
| Cousine | 332.5 | 329.1 | 329.1 | 329.1 | 330.0 | 3.4 | 0.625 | 0.501 | 64 | -64.4 | 219 | 486 | 489 | 71.3 | 486 | 72.3 | 178 | 486 | 508 | 357 | 351 |
| Go Mono | 301.3 | 301.3 | 301.3 | 301.3 | 301.3 | 0.0 | 0.568 | 0.417 | -66 | 0.0 | 91 | 503 | 504 | 72.3 | 503 | 72.3 | 120 | 504 | 602 | 498 | 476 |
| Iosevka | 340.0 | 340.0 | 340.0 | 340.0 | 340.0 | 0.0 | 0.654 | 0.463 | -35 | 0.0 | 276 | 372 | 386 | 66.0 | 372 | 67.0 | 112 | 391 | 514 | 424 | 400 |
| JuliaMono | 274.5 | 276.0 | 275.0 | 275.0 | 275.1 | 1.5 | 0.500 | 0.379 | -87 | -0.1 | 0 | 465 | 477 | 96.0 | 459 | 95.0 | 106 | 462 | 489 | 542 | 526 |
| Fira Mono (dup) | 311.0 | 311.0 | 313.5 | 313.5 | 312.2 | 2.5 | 0.592 | 0.453 | -23 | 0.8 | 18 | 368 | 368 | 70.0 | 388 | 72.0 | 118 | 425 | 561 | 408 | 393 |
| Cascadia Mono (dup) | 346.2 | 346.2 | 346.2 | 346.2 | 346.2 | 0.0 | 0.669 | 0.499 | -0 | 0.0 | 4 | 488 | 507 | 90.8 | 488 | 90.8 | 153 | 468 | 483 | 477 | 448 |
| Liberation Mono (dup) | 332.5 | 329.1 | 329.1 | 329.1 | 330.0 | 3.4 | 0.625 | 0.501 | 64 | -64.4 | 219 | 486 | 489 | 71.3 | 486 | 72.3 | 178 | 486 | 508 | 357 | 351 |
| Hack (dup) | 313.5 | 313.0 | 313.5 | 313.5 | 313.4 | 0.5 | 0.573 | 0.430 | -33 | -19.9 | 136 | 516 | 517 | 83.0 | 516 | 84.0 | 115 | 516 | 489 | 475 | 489 |
| Monaspace Neon (extra) | 327.5 | 327.2 | 327.2 | 327.2 | 327.3 | 0.3 | 0.637 | 0.448 | -45 | 0.2 | 12 | 473 | 480 | 82.0 | 440 | 82.0 | 192 | 435 | 622 | 526 | 500 |
| 0xProto (extra) | 307.0 | 308.0 | 304.0 | 304.0 | 305.8 | 4.0 | 0.556 | 0.431 | -44 | 1.2 | -8 | 470 | 502 | 86.0 | 470 | 86.0 | 116 | 420 | 586 | 492 | 472 |
| mononoki (extra) | 244.1 | 244.6 | 244.1 | 244.1 | 244.2 | 0.5 | 0.500 | 0.357 | -73 | 0.4 | 16 | 462 | 488 | 75.2 | 462 | 75.2 | 149 | 417 | 621 | 478 | 457 |
| B612 Mono (extra) | 310.8 | 240.0 | 325.5 | 325.5 | 300.4 | 85.5 | 0.536 | 0.395 | -57 | -39.2 | 240 | 450 | 500 | 77.5 | 400 | 70.0 | 80 | 450 | 560 | 380 | 369 |

The four operators share a centre within 2 units in 20 of 34. The hyphen-minus is within 2 units of that axis in 20; the fonts that keep a low, text-style hyphen are DejaVu Sans Mono (-40), Red Hat Mono (-68), Space Mono (-90), Noto Sans Mono (-87), Spline Sans Mono (-11), Overpass Mono (-48), Share Tech Mono (-11), PT Mono (-45), Cousine (-64). The asterisk is the split decision: within 12 units of the axis in 12 of 34 and more than 100 above it (a raised, text-style star) in 14.

### 4.9 Brackets and the bar

| font | | top | | bottom | | stroke | [ top | [ bottom | { top | { bottom | ( top | ( bottom | / top | / bottom | [ centre - axis | [ top - cap | [ bottom - desc p | [ stroke | [ w | ( w | { w |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **JetBrains Mono** | 830 | -110 | 90.0 | 830 | -110 | 830 | -110 | 840 | -120 | 830 | -110 | 30 | 100 | 70 | 90.0 | 245 | 300 | 430 |
| **IBM Plex Mono** | 760 | -138 | 70.0 | 760 | -138 | 760 | -138 | 760 | -138 | 760 | -138 | 6 | 62 | 62 | 69.0 | 280 | 289 | 390 |
| **Source Code Pro** | 750 | -250 | 74.0 | 708 | -152 | 708 | -152 | 732 | -176 | 710 | -160 | -53 | 52 | 53 | 66.0 | 277 | 270 | 382 |
| **Fira Code** | 900 | -300 | 75.0 | 816 | -116 | 836 | -136 | 840 | -140 | 810 | -103 | 38 | 127 | 96 | 79.5 | 250 | 302 | 334 |
| **Cascadia Code** | 845 | -151 | 101.6 | 798 | -104 | 794 | -104 | 791 | -98 | 786 | -93 | 0 | 104 | 120 | 101.6 | 306 | 357 | 361 |
| **Commit Mono** | 790 | -170 | 78.0 | 790 | -170 | 790 | -170 | 790 | -170 | 790 | -170 | 0 | 90 | 30 | 84.0 | 297 | 300 | 429 |
| **Recursive Mono Linear** | 760 | -161 | 96.0 | 756 | -148 | 760 | -161 | 756 | -141 | 750 | -130 | 4 | 56 | 52 | 96.0 | 315 | 293 | 442 |
| **Intel One Mono** | 755 | -100 | 80.0 | 787 | -135 | 801 | -139 | 805 | -147 | 755 | -100 | 2 | 132 | 95 | 87.0 | 335 | 408 | 473 |
| **DejaVu Sans Mono** | 764 | -236 | 84.0 | 760 | -132 | 760 | -163 | 759 | -132 | 729 | -93 | 1 | 31 | 76 | 89.8 | 207 | 224 | 386 |
| Roboto Mono | 711 | -194 | 72.8 | 812 | -152 | 780 | -179 | 802 | -230 | 711 | -61 | 10 | 102 | 51 | 85.4 | 193 | 258 | 330 |
| Red Hat Mono | 700 | -209 | 68.0 | 700 | -215 | 711 | -219 | 714 | -222 | 700 | -209 | -106 | 0 | -6 | 70.0 | 291 | 319 | 352 |
| Space Mono | 856 | -156 | 72.0 | 856 | -156 | 856 | -156 | 856 | -156 | 806 | -106 | 0 | 156 | 44 | 78.0 | 174 | 390 | 252 |
| Ubuntu Mono | 699 | -165 | 77.0 | 699 | -165 | 699 | -165 | 701 | -167 | 699 | -165 | 8 | 80 | 0 | 78.0 | 239 | 273 | 348 |
| Victor Mono | 948 | -182 | 75.0 | 945 | -145 | 945 | -145 | 945 | -145 | 948 | -182 | -0 | 145 | 37 | 75.0 | 305 | 298 | 383 |
| Geist Mono | 750 | -110 | 80.0 | 750 | -110 | 750 | -120 | 750 | -110 | 750 | -110 | 27 | 40 | 40 | 80.0 | 320 | 280 | 380 |
| Atkinson Hyperlegible Mono | 838 | -162 | 84.0 | 708 | -162 | 708 | -162 | 708 | -162 | 708 | -90 | 24 | 40 | 0 | 78.0 | 277 | 313 | 342 |
| Martian Mono | 860 | -60 | 94.0 | 900 | -140 | 912 | -152 | 920 | -160 | 848 | -170 | 30 | 100 | 60 | 108.0 | 293 | 333 | 393 |
| Inconsolata | 652 | -151 | 67.0 | 670 | -89 | 701 | -95 | 735 | -104 | 665 | -42 | -20 | 47 | 78 | 64.0 | 287 | 292 | 355 |
| Noto Sans Mono | 760 | -240 | 73.0 | 714 | -158 | 714 | -158 | 714 | -158 | 714 | 0 | -79 | 0 | 82 | 86.0 | 225 | 230 | 320 |
| Courier Prime | 681 | -173 | 73.2 | 670 | -163 | 670 | -163 | 674 | -168 | 681 | -173 | -31 | 90 | 27 | 73.2 | 264 | 277 | 397 |
| DM Mono | 720 | -270 | 84.0 | 811 | -185 | 811 | -185 | 811 | -185 | 760 | -90 | -36 | 111 | 35 | 79.0 | 254 | 284 | 374 |
| Sometype Mono | 750 | -250 | 72.0 | 710 | -210 | 710 | -210 | 722 | -222 | 710 | -60 | -25 | 60 | 0 | 72.0 | 315 | 321 | 405 |
| Fragment Mono | 779 | -80 | 82.0 | 779 | -80 | 779 | -80 | 780 | -80 | 794 | -80 | 27 | 80 | 138 | 72.0 | 206 | 248 | 317 |
| Azeret Mono | 736 | -190 | 106.0 | 699 | -97 | 698 | -97 | 698 | -97 | 699 | -97 | -7 | 1 | 81 | 100.0 | 244 | 217 | 303 |
| Spline Sans Mono | 850 | -127 | 84.5 | 831 | -124 | 836 | -128 | 833 | -125 | 846 | -98 | -15 | 104 | 78 | 90.5 | 336 | 334 | 378 |
| Anonymous Pro | 728 | -91 | 67.4 | 728 | -182 | 728 | -182 | 734 | -181 | 661 | -117 | 39 | 91 | 0 | 53.7 | 182 | 252 | 272 |
| Overpass Mono | 1062 | -378 | 81.5 | 712 | -130 | 712 | -130 | 712 | -130 | 712 | -130 | -55 | 12 | 72 | 81.5 | 220 | 278 | 309 |
| Oxygen Mono | 774 | -215 | 78.6 | 845 | -66 | 833 | -75 | 832 | -74 | 774 | -109 | 20 | 117 | 149 | 92.3 | 256 | 234 | 428 |
| Share Tech Mono | 810 | -110 | 80.0 | 820 | -120 | 820 | -120 | 820 | -120 | 810 | -110 | 26 | 120 | 50 | 80.0 | 210 | 200 | 245 |
| PT Mono | 700 | -130 | 68.0 | 700 | -230 | 701 | -230 | 712 | -220 | 712 | -140 | -98 | 0 | -30 | 78.0 | 381 | 400 | 440 |
| Cousine | 725 | -208 | 81.1 | 725 | -208 | 725 | -208 | 725 | -208 | 725 | -10 | -71 | 66 | 0 | 87.9 | 267 | 268 | 407 |
| Go Mono | 771 | -144 | 72.3 | 771 | -144 | 771 | -144 | 771 | -144 | 771 | -144 | 12 | 48 | 48 | 84.5 | 265 | 323 | 400 |
| Iosevka | 823 | -143 | 78.0 | 823 | -143 | 833 | -153 | 841 | -161 | 823 | -143 | 0 | 88 | 72 | 78.0 | 276 | 295 | 316 |
| JuliaMono | 884 | -264 | 95.0 | 838 | -209 | 846 | -203 | 838 | -243 | 775 | -190 | 39 | 113 | -19 | 90.0 | 290 | 298 | 385 |
| Fira Mono (dup) | 807 | -102 | 75.0 | 815 | -115 | 836 | -136 | 840 | -140 | 809 | -103 | 38 | 126 | 97 | 80.0 | 251 | 301 | 334 |
| Cascadia Mono (dup) | 845 | -151 | 101.6 | 798 | -104 | 794 | -104 | 791 | -98 | 786 | -93 | 0 | 104 | 120 | 101.6 | 306 | 357 | 361 |
| Liberation Mono (dup) | 725 | -208 | 81.1 | 725 | -208 | 725 | -208 | 725 | -208 | 725 | -10 | -71 | 66 | 0 | 87.9 | 267 | 268 | 407 |
| Hack (dup) | 764 | -236 | 84.0 | 799 | -132 | 799 | -124 | 759 | -132 | 729 | -93 | 20 | 70 | 76 | 89.8 | 305 | 224 | 413 |
| Monaspace Neon (extra) | 801 | -200 | 97.0 | 801 | -200 | 801 | -200 | 801 | -200 | 730 | -100 | -27 | 71 | -6 | 93.5 | 328 | 340 | 488 |
| 0xProto (extra) | 766 | -160 | 98.0 | 750 | -120 | 765 | -135 | 760 | -138 | 750 | -120 | 9 | 40 | 77 | 95.0 | 279 | 335 | 374 |
| mononoki (extra) | 732 | -174 | 83.0 | 732 | -174 | 732 | -174 | 732 | -195 | 680 | -191 | 35 | 49 | 70 | 83.0 | 337 | 405 | 445 |
| B612 Mono (extra) | 760 | -200 | 100.0 | 760 | -210 | 758 | -210 | 800 | -210 | 800 | -50 | -25 | 0 | 40 | 99.0 | 286 | 220 | 413 |

Brackets, braces and parentheses share their top and bottom to within 15 units in 25 of 34. They rise a median of 84 above the cap height and stop 51 above the descender line. Their centre is within 12 units of the math axis in 13 of 34. The bar is as tall as the brackets in most fonts and much taller in Source Code Pro (-250..750), Fira Code (-300..900), Atkinson Hyperlegible Mono (-162..838), Noto Sans Mono (-240..760), Azeret Mono (-190..736), Overpass Mono (-378..1062).

### 4.10 Box drawing, blocks, Powerline

Only fonts that have the glyphs are listed. "over" columns are how far the glyph extends beyond the advance (left, right) or beyond the hhea ascender (top) and descender (bottom); negative means it stops short.

| font | U+2500 xmin | xmax | over left | over right | thick | y centre | y - cell centre | y - math axis | U+2502 ymin | ymax | over top | over bottom | height / line | thick | x - adv/2 | U+2588 bounds (x, y) | U+2588 over top / bottom | U+E0B0 bounds (x, y) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **JetBrains Mono** | -20 | 620 | 20 | 20 | 100 | 370.0 | 10 | 40 | -300 | 1020 | 0 | 0 | 1.000 | 100 | 0.0 | -10..610 x -300..1020 | 0 / 0 | 0..600 x -270..970 |
| **IBM Plex Mono** | -34 | 634 | 34 | 34 | 68 | 300.0 | -75 | -5 | -350 | 950 | -75 | 75 | 1.000 | 68 | 0.0 | 0..600 x -350..950 | -75 / 75 | – |
| **Source Code Pro** | -39 | 639 | 39 | 39 | 78 | 300.0 | -56 | -31 | -400 | 1000 | 16 | 127 | 1.114 | 78 | 0.0 | 0..600 x -400..1000 | 16 / 127 | 0..600 x -280..1040 |
| **Fira Code** | -5 | 605 | 5 | 5 | 80 | 350.0 | 16 | 38 | -500 | 1000 | 10 | 178 | 1.143 | 80 | 0.0 | 0..600 x -300..900 | -90 / -22 | 0..500 x -300..900 |
| **Cascadia Code** | -51 | 637 | 51 | 51 | 102 | 345.2 | -2 | -1 | -259 | 1087 | 159 | 24 | 1.158 | 102 | 0.0 | 0..586 x -234..1087 | 159 / 0 | – |
| **Commit Mono** | -10 | 610 | 10 | 10 | 60 | 350.0 | 0 | 40 | -500 | 1200 | 300 | 300 | 1.546 | 60 | 0.0 | 0..600 x -200..900 | 0 / 0 | 0..550 x -200..900 |
| **Intel One Mono** | -20 | 634 | 20 | 20 | 87 | 330.5 | -70 | 6 | -420 | 1080 | -10 | 130 | 1.087 | 87 | 0.5 | 0..614 x -360..1020 | -70 / 70 | 126..560 x 0..655 |
| **DejaVu Sans Mono** | -10 | 612 | 10 | 10 | 84 | 343.8 | -2 | 30 | -250 | 938 | 10 | 14 | 1.021 | 78 | -0.2 | -10..612 x -250..938 | 10 / 14 | – |
| Ubuntu Mono | 0 | 500 | 0 | 0 | 80 | 330.0 | 0 | 72 | -170 | 830 | 0 | 0 | 1.000 | 80 | 0.0 | 0..500 x -170..830 | 0 / 0 | – |
| Victor Mono | -37 | 638 | 37 | 38 | 75 | 400.5 | -24 | 0 | -475 | 1275 | 175 | 225 | 1.296 | 75 | 0.5 | 0..600 x -475..1275 | 175 / 225 | -1..600 x -340..1110 |
| Geist Mono | -5 | 605 | 5 | 5 | 84 | 310.0 | -45 | 17 | -345 | 965 | -40 | 50 | 1.008 | 84 | 0.0 | 0..600 x -340..960 | -45 / 45 | – |
| Inconsolata | -80 | 580 | 80 | 80 | 120 | 300.0 | -34 | -11 | -400 | 1000 | 141 | 210 | 1.335 | 120 | 0.0 | 0..500 x -400..1000 | 141 / 210 | – |
| Noto Sans Mono | -6 | 606 | 6 | 6 | 71 | 366.5 | -22 | 9 | -246 | 979 | -90 | -47 | 0.899 | 71 | -0.5 | 0..600 x -240..973 | -96 / -53 | – |
| Anonymous Pro | 0 | 546 | 0 | 0 | 67 | 318.6 | 1 | 85 | -182 | 818 | 0 | 0 | 1.000 | 67 | -45.4 | – | – | – |
| Overpass Mono | -10 | 626 | 10 | 10 | 84 | 282.2 | 32 | -64 | -378 | 942 | 59 | -5 | 1.043 | 84 | 0.2 | – | – | 0..553 x -378..1158 |
| PT Mono | 0 | 600 | 0 | 0 | 76 | 342.0 | 17 | 9 | -235 | 885 | 0 | 0 | 1.000 | 76 | 0.0 | 0..600 x -235..885 | 0 / 0 | – |
| Cousine | -5 | 605 | 5 | 5 | 71 | 306.4 | 40 | -24 | -300 | 832 | 0 | 0 | 1.000 | 71 | 0.0 | 0..600 x -300..832 | 0 / 0 | – |
| Go Mono | 0 | 600 | 0 | 0 | 72 | 367.2 | 0 | 66 | -211 | 945 | 0 | 0 | 1.000 | 72 | 0.2 | 0..600 x -211..945 | 0 / 0 | – |
| Iosevka | 0 | 500 | 0 | 0 | 62 | 340.0 | -35 | 0 | -285 | 965 | 0 | 70 | 1.000 | 70 | 0.0 | 0..500 x -285..965 | 0 / 70 | -8..500 x -285..965 |
| JuliaMono | -12 | 611 | 12 | 11 | 100 | 275.0 | -88 | -0 | -500 | 1200 | 250 | 275 | 1.446 | 78 | -1.0 | 0..600 x -225..950 | 0 / 0 | -1..532 x -240..950 |
| Fira Mono (dup) | -5 | 605 | 5 | 5 | 80 | 350.0 | 15 | 38 | -500 | 1000 | 65 | 235 | 1.250 | 80 | 0.0 | 0..600 x -500..1000 | 65 / 235 | – |
| Cascadia Mono (dup) | -51 | 637 | 51 | 51 | 102 | 345.2 | -2 | -1 | -259 | 1087 | 159 | 24 | 1.158 | 102 | 0.0 | 0..586 x -234..1087 | 159 / 0 | – |
| Liberation Mono (dup) | -5 | 605 | 5 | 5 | 71 | 306.4 | 40 | -24 | -300 | 832 | 0 | 0 | 1.000 | 71 | 0.0 | 0..600 x -300..832 | 0 / 0 | – |
| Hack (dup) | -10 | 612 | 10 | 10 | 84 | 343.8 | -2 | 30 | -259 | 952 | 24 | 23 | 1.040 | 78 | -0.2 | 0..602 x -250..952 | 24 / 14 | -39..602 x -240..935 |
| Monaspace Neon (extra) | -5 | 625 | 5 | 5 | 80 | 322.5 | -50 | -5 | -305 | 950 | 5 | 105 | 1.008 | 80 | 0.0 | -5..625 x -305..950 | 5 / 105 | -5..500 x -305..950 |
| 0xProto (extra) | -10 | 630 | 10 | 10 | 68 | 348.0 | -2 | 42 | -430 | 1130 | 0 | 0 | 1.000 | 68 | 0.0 | – | – | – |
| mononoki (extra) | -20 | 582 | 20 | 20 | 41 | 317.4 | 0 | 73 | -244 | 879 | 0 | 0 | 1.000 | 41 | -0.5 | 0..562 x -244..879 | 0 / 0 | -20..553 x -244..879 |

Of the 20 core designs with U+2502: the vertical line reaches or passes both the hhea ascender and descender in 15; it matches them exactly in 6 (JetBrains Mono, Ubuntu Mono, Anonymous Pro, PT Mono, Cousine, Go Mono); it stops short at one end in IBM Plex Mono (-75 top, 75 bottom), Intel One Mono (-10 top, 130 bottom), Geist Mono (-40 top, 50 bottom), Noto Sans Mono (-90 top, -47 bottom), Overpass Mono (59 top, -5 bottom). The largest overshoots are Commit Mono (300 at each end), JuliaMono (250 top, 275 bottom) and Victor Mono (175 top, 225 bottom). The horizontal line overhangs the advance on both sides in 15 of 20 and ends exactly on it in 5. The Unicode Standard describes the intent: "The lines in the box drawing characters typically extend to the middle of the top, bottom, left, and/or right of the bounding box for the character cell. They are designed to connect together into continuous lines, with no gaps between them. When emulating terminal applications, fonts that implement the box drawing characters should do likewise" ([Unicode 16.0, section 22.8.1](https://www.unicode.org/versions/Unicode16.0.0/core-spec/chapter-22/)).

Coverage (number of code points present in each block):

| font | box 2500-257F (128) | blocks 2580-259F (32) | braille 2800-28FF (256) | Powerline E0A0-E0B3 (20) | legacy computing 1FB00-1FBFF | arrows 2190-21FF (112) | math operators 2200-22FF (256) | Greek 0370-03FF | cmap total |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **JetBrains Mono** | 128 | 32 | 0 | 7 | 0 | 11 | 35 | 77 | 976 |
| **IBM Plex Mono** | 128 | 32 | 0 | 0 | 0 | 22 | 13 | 1 | 930 |
| **Source Code Pro** | 128 | 32 | 0 | 7 | 0 | 15 | 20 | 84 | 1334 |
| **Fira Code** | 128 | 32 | 0 | 7 | 0 | 24 | 58 | 121 | 1551 |
| **Cascadia Code** | 128 | 32 | 256 | 0 | 168 | 10 | 20 | 77 | 2426 |
| **Commit Mono** | 127 | 32 | 256 | 7 | 0 | 16 | 63 | 72 | 1175 |
| **Recursive Mono Linear** | 0 | 0 | 0 | 0 | 0 | 10 | 17 | 20 | 745 |
| **Intel One Mono** | 128 | 32 | 0 | 7 | 0 | 0 | 5 | 1 | 793 |
| **DejaVu Sans Mono** | 128 | 32 | 0 | 0 | 0 | 112 | 178 | 116 | 3322 |
| Roboto Mono | 0 | 0 | 0 | 0 | 0 | 0 | 13 | 75 | 876 |
| Red Hat Mono | 0 | 0 | 0 | 0 | 0 | 2 | 3 | 0 | 404 |
| Space Mono | 0 | 0 | 0 | 0 | 0 | 10 | 14 | 1 | 624 |
| Ubuntu Mono | 40 | 4 | 0 | 0 | 0 | 0 | 14 | 71 | 1224 |
| Victor Mono | 128 | 32 | 0 | 7 | 0 | 101 | 28 | 77 | 1269 |
| Geist Mono | 128 | 32 | 0 | 0 | 0 | 21 | 13 | 5 | 889 |
| Atkinson Hyperlegible Mono | 0 | 0 | 0 | 0 | 0 | 0 | 13 | 4 | 359 |
| Martian Mono | 0 | 0 | 0 | 0 | 0 | 4 | 3 | 0 | 511 |
| Inconsolata | 128 | 32 | 0 | 0 | 0 | 15 | 18 | 1 | 882 |
| Noto Sans Mono | 128 | 32 | 0 | 0 | 0 | 23 | 104 | 121 | 3490 |
| Courier Prime | 0 | 0 | 0 | 0 | 0 | 0 | 12 | 4 | 383 |
| DM Mono | 0 | 0 | 0 | 0 | 0 | 0 | 13 | 1 | 381 |
| Sometype Mono | 0 | 0 | 0 | 0 | 0 | 10 | 15 | 4 | 456 |
| Fragment Mono | 0 | 0 | 0 | 0 | 0 | 19 | 15 | 3 | 487 |
| Azeret Mono | 0 | 0 | 0 | 0 | 0 | 8 | 13 | 4 | 433 |
| Spline Sans Mono | 0 | 0 | 0 | 0 | 0 | 0 | 4 | 0 | 411 |
| Anonymous Pro | 40 | 0 | 0 | 0 | 0 | 0 | 12 | 71 | 623 |
| Overpass Mono | 128 | 0 | 0 | 7 | 0 | 36 | 256 | 4 | 1642 |
| Oxygen Mono | 0 | 0 | 0 | 0 | 0 | 0 | 12 | 0 | 359 |
| Share Tech Mono | 0 | 0 | 0 | 0 | 0 | 0 | 17 | 2 | 267 |
| PT Mono | 40 | 8 | 0 | 0 | 0 | 7 | 17 | 4 | 805 |
| Cousine | 40 | 8 | 0 | 0 | 0 | 7 | 17 | 127 | 2282 |
| Go Mono | 40 | 8 | 0 | 0 | 0 | 7 | 18 | 73 | 709 |
| Iosevka | 128 | 32 | 256 | 10 | 247 | 112 | 256 | 121 | 7512 |
| JuliaMono | 128 | 32 | 256 | 8 | 250 | 112 | 256 | 135 | 11191 |
| Fira Mono (dup) | 116 | 32 | 0 | 0 | 0 | 15 | 15 | 121 | 1350 |
| Cascadia Mono (dup) | 128 | 32 | 256 | 0 | 168 | 10 | 20 | 77 | 2426 |
| Liberation Mono (dup) | 40 | 8 | 0 | 0 | 0 | 8 | 18 | 127 | 2305 |
| Hack (dup) | 128 | 32 | 0 | 7 | 0 | 109 | 177 | 73 | 1548 |
| Monaspace Neon (extra) | 128 | 32 | 0 | 8 | 10 | 70 | 211 | 81 | 2460 |
| 0xProto (extra) | 128 | 0 | 0 | 0 | 0 | 0 | 5 | 1 | 719 |
| mononoki (extra) | 128 | 32 | 0 | 8 | 0 | 15 | 58 | 75 | 921 |
| B612 Mono (extra) | 0 | 0 | 0 | 19 | 0 | 34 | 47 | 51 | 589 |

### 4.11 Underline and strikeout

| font | underline position | underline thickness | strikeout position | strikeout size | strikeout / x | underscore top | underscore thick | descender p |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **JetBrains Mono** | -155 | 50 | 320 | 50 | 0.582 | -25 | 75.0 | -180 |
| **IBM Plex Mono** | -140 | 60 | 309 | 60 | 0.599 | -95 | 74.0 | -200 |
| **Source Code Pro** | -50 | 50 | 291 | 50 | 0.599 | -69 | 71.0 | -205 |
| **Fira Code** | -50 | 25 | 316 | 25 | 0.600 | -108 | 73.5 | -212 |
| **Cascadia Code** | -49 | 49 | 310 | 49 | 0.600 | 0 | 90.8 | -225 |
| **Commit Mono** | -100 | 50 | 324 | 50 | 0.600 | -46 | 76.0 | -200 |
| **Recursive Mono Linear** | -193 | 72 | 301 | 72 | 0.566 | -79 | 88.0 | -200 |
| **Intel One Mono** | -75 | 50 | 286 | 50 | 0.615 | -26 | 80.0 | -230 |
| **DejaVu Sans Mono** | -20 | 44 | 259 | 50 | 0.473 | -197 | 39.1 | -208 |
| Roboto Mono | -73 | 49 | 250 | 50 | 0.473 | 0 | 73.7 | -203 |
| Red Hat Mono | -200 | 100 | 317 | 50 | 0.650 | -80 | 57.0 | -209 |
| Space Mono | -75 | 58 | 250 | 50 | 0.504 | -48 | 72.0 | -200 |
| Ubuntu Mono | -123 | 20 | 250 | 50 | 0.539 | -95 | 70.0 | -165 |
| Victor Mono | -100 | 50 | 371 | 50 | 0.600 | -113 | 69.0 | -182 |
| Geist Mono | -100 | 50 | 318 | 50 | 0.600 | 0 | 78.0 | -150 |
| Atkinson Hyperlegible Mono | -78 | 50 | 258 | 50 | 0.520 | 0 | 77.0 | -162 |
| Martian Mono | -100 | 50 | 360 | 50 | 0.600 | -50 | 100.0 | -200 |
| Inconsolata | -200 | 50 | 274 | 50 | 0.600 | -19 | 61.0 | -167 |
| Noto Sans Mono | -100 | 50 | 322 | 50 | 0.601 | -74 | 80.0 | -240 |
| Courier Prime | -90 | 64 | 270 | 64 | 0.600 | -123 | 66.4 | -190 |
| DM Mono | -100 | 50 | 298 | 50 | 0.601 | 0 | 77.0 | -220 |
| Sometype Mono | -105 | 60 | 282 | 60 | 0.600 | -72 | 66.0 | -210 |
| Fragment Mono | -100 | 50 | 314 | 50 | 0.599 | -146 | 72.0 | -218 |
| Azeret Mono | -100 | 50 | 326 | 50 | 0.593 | 0 | 88.0 | -178 |
| Spline Sans Mono | -50 | 25 | 256 | 51 | 0.469 | -26 | 74.0 | -202 |
| Anonymous Pro | -91 | 60 | 227 | 60 | 0.499 | -34 | 57.1 | -182 |
| Overpass Mono | -94 | 84 | 306 | 84 | 0.600 | -96 | 81.5 | -202 |
| Oxygen Mono | -87 | 58 | 321 | 58 | 0.600 | -77 | 67.9 | -215 |
| Share Tech Mono | -110 | 50 | 300 | 50 | 0.600 | -95 | 75.0 | -170 |
| PT Mono | -75 | 50 | 250 | 50 | 0.500 | -135 | 70.0 | -200 |
| Cousine | -233 | 41 | 259 | 50 | 0.490 | -60 | 46.9 | -208 |
| Go Mono | -134 | 24 | 250 | 50 | 0.471 | 0 | 72.3 | -193 |
| Iosevka | -50 | 50 | 265 | 51 | 0.510 | 0 | 70.0 | -215 |
| JuliaMono | -100 | 50 | 275 | 50 | 0.500 | 66 | 86.0 | -190 |
| Fira Mono (dup) | -75 | 50 | 316 | 50 | 0.600 | -108 | 74.0 | -212 |
| Cascadia Mono (dup) | -49 | 49 | 310 | 49 | 0.600 | 0 | 90.8 | -225 |
| Liberation Mono (dup) | -192 | 41 | 259 | 50 | 0.490 | -60 | 46.9 | -208 |
| Hack (dup) | -107 | 44 | 259 | 50 | 0.473 | -93 | 58.6 | -208 |
| Monaspace Neon (extra) | -35 | 36 | 258 | 50 | 0.501 | -115 | 65.0 | -194 |
| 0xProto (extra) | -100 | 50 | 330 | 50 | 0.600 | 0 | 86.0 | -197 |
| mononoki (extra) | -98 | 49 | 244 | 49 | 0.500 | 0 | 75.2 | -244 |
| B612 Mono (extra) | -125 | 50 | 250 | 50 | 0.446 | -150 | 77.5 | -250 |

The specification asks that "the underline thickness should match the thickness of the underscore character (U+005F LOW LINE), and should also match the strikeout thickness" ([OpenType post](https://learn.microsoft.com/en-us/typography/opentype/spec/post)). Underline thickness is within 2 units of the underscore's in 0 of 34 and equals the strikeout size in 25; the common practice is a 50-unit line (19 of 34) that is thinner than the underscore glyph (median 74).

## 5. Contact sheets: zero, 1 l I, and what else stands out

Rendered with FreeType at 48 px: line 1 `0O 1lI| 5S 8B 2Z 6b9g rnm {}[]() <>= -> != :: ,.;: '`"` and line 2 `Hamburgefonstiv 0123456789` are unshaped (what a terminal without ligature support shows); line 3 is shaped with the font's default features, followed by box-drawing and shade glyphs if the font has them. I looked at every sheet. The 1 / l / I / i columns are measured from the outlines (how far the ink reaches left and right of the mid-height stem at the top and at the bottom) and agree with what the sheets show.

Files: `contact-a-callout1.png`, `contact-b-callout2.png`, `contact-c-dejavu-family.png`, `contact-d-neo-grotesque.png`, `contact-e-wide-legible.png`, `contact-f-narrow-humanist.png`, `contact-g-geometric.png`, `contact-h-misc.png`, `contact-i-typewriter-metric.png`, `contact-j-extras.png`; enlargements `contact-zoom-1.png` to `contact-zoom-3.png` (`0O1lI|ijagft*` at 96 px) and `contact-zeros.png` (every zero at 170 px).

| font | zero | 1 | l | I | i | a | g | sequences changed by default shaping | notable |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **JetBrains Mono** | dotted (round dot) | flag, full foot | flag, right tail | top bar, full foot | flag, full foot | double | single | 19 of 22: `->` `=>` `!=` `<=` `>=` `==` `===` `::` ... | Ascender = cap height (730). Rectangular bowls (the squarest o and O of the callout set). l has a curved right tail. Ligatures on by default. |
| **IBM Plex Mono** | dotted (rounded-rectangle dot) | flag, full foot | flag, full foot | top bar, full foot | flag, full foot | double | double | none | Slab feet on i, l, r; double-storey g; braces with a sharp cusp. Box glyphs are centred on y=300, 75 below the hhea cell centre. |
| **Source Code Pro** | dotted (round dot) | flag, full foot | flag, right tail | top bar, full foot | flag, plain bottom | double | double | none | Smallest x-height of the callout set after Intel One (486); wide round o; i has no foot and its stem sits right of centre; thin hyphen (62). Double-storey g. |
| **Fira Code** | slashed | flag, full foot | flag, right tail | top bar, full foot | flag, full foot | double | double | 22 of 22: `->` `=>` `!=` `<=` `>=` `==` `===` `::` ... | Slashed zero in this build while Fira Mono's is dotted. r with a foot serif. Bar | spans -300..900. Ligatures on by default (22 of 22 test sequences change). |
| **Cascadia Code** | dotted (large round dot) | flag, full foot | flag, right tail | top bar, full foot | flag, full foot | double | single | 20 of 22: `->` `=>` `!=` `<=` `>=` `==` `===` `::` ... | Heaviest regular of the callout set (n stem 103.5); 586 advance; math axis sits exactly on the cell centre and on the box-drawing line. Ligatures on by default. |
| **Commit Mono** | slashed | flag, full foot | flag, right tail | top bar, full foot | flag, full foot | double | double | 7 of 22: `::` `|>` `//` `www` `...` `||` `<>` | Tightest default line (1.10). Box-drawing verticals overshoot the hhea box by 300 units at each end. Slash of the zero stays inside the counter. Double-storey g. |
| **Recursive Mono Linear** | slashed (slash with a kink at both ends) | flag, full foot | flag, right tail | top bar, full foot | flag, plain bottom | double | double | 1 of 22: `fi` | Mono Linear instance (MONO=1, CASL=0). No box-drawing glyphs in this file. i without a foot; double-storey g; square period. |
| **Intel One Mono** | slashed | flag, full foot | flag, right tail | top bar, full foot | flag, full foot | double | single | 1 of 22: `::` | Low x-height (465) on a wide 614 advance, large round o (width/height 0.98), tall default line (1.38), exaggerated braces. |
| **DejaVu Sans Mono** | dotted (oval dot) | flag, full foot | flag, right tail | top bar, full foot | flag, full foot | double | single | none | H stem 99 against n stem 90; asterisk raised 201 above the math axis; underscore full-width and low (-197..-236); OS/2 version 1, so no sxHeight. |
| Roboto Mono | slashed | flag, plain bottom | flag, full foot | top bar, full foot | flag, full foot | double | single | none | 1 without a foot, l with a full foot. No box-drawing glyphs. |
| Red Hat Mono | slashed | flag, full foot | flag, right tail | top bar, full foot | flag, right tail | double | single | 2 of 22: `->` `<-` | Light (n stem 73). No box-drawing glyphs. -> ligated to an arrow. |
| Space Mono | dotted (round dot) | flag, full foot | flag, full foot | top bar, full foot | flag, full foot | single | single | none | Single-storey a (the only one); squared parentheses; 612 advance. No box-drawing glyphs. |
| Ubuntu Mono | dotted (oval dot) | flag, full foot | flag, right tail | top bar, full foot | flag, right tail | double | single | none | 500 advance. OS/2 sxHeight (520) and sCapHeight (693) do not match the outlines (464, 619). |
| Victor Mono | dotted (small round dot) | flag, full foot | flag, right tail | top bar, full foot | flag, full foot | double | single | 14 of 22: `->` `=>` `!=` `<=` `>=` `==` `===` `::` ... | Tall and narrow: x-height 618 and cap height 800 on a 600 advance; thin (75). Ligatures on by default. |
| Geist Mono | slashed | flag, full foot | flag, full foot | top bar, full foot | flag, full foot | double | single | none | l with a full foot; square period. |
| Atkinson Hyperlegible Mono | reverse-slashed (top-left to bottom-right) | flag, full foot | flag, right tail | top bar, full foot | flag, full foot | double | single | none | Wide 632 advance; the only reversed slash. No box-drawing glyphs. |
| Martian Mono | slashed | flag, full foot | flag, full foot | top bar, full foot | flag, full foot | double | single | none | Widest and heaviest (700 advance, n stem 110, x-height 600). No box-drawing glyphs. |
| Inconsolata | slashed | flag, plain bottom | flag, full foot | top bar, full foot | flag, full foot | double | double | none | 500 advance, light (n stem 70); 1 without a foot; double-storey g. |
| Noto Sans Mono | slashed | flag, full foot | flag, full foot | top bar, full foot | flag, full foot | double | single | none | Box verticals stop 90 short of the hhea ascender and 47 short of the descender. |
| Courier Prime | plain | flag, full foot | flag, full foot | top bar, full foot | flag, full foot | double | single | none | Typewriter slab: smallest caps (580) and x-height (451); zero differs from O by width only. No box-drawing glyphs. |
| DM Mono | slashed | flag, full foot | flag, full foot | top bar, full foot | flag, full foot | double | double | none | f descends to -220; double-storey g. No box-drawing glyphs. |
| Sometype Mono | slashed | flag, full foot | flag, right tail | top bar, full foot | flag, right tail | double | single | none | 580 advance; light (72). No box-drawing glyphs. |
| Fragment Mono | slashed | flag, plain bottom | flag, full foot | top bar, full foot | flag, full foot | double | single | 15 of 22: `->` `=>` `!=` `<=` `>=` `==` `===` `::` ... | 1 without a foot. Ligatures on by default. No box-drawing glyphs. |
| Azeret Mono | plain | flag, full foot | flag, full foot | top bar, full foot | flag, full foot | double | single | 4 of 22: `->` `<-` `fi` `0x1F` | Plain zero that differs from O only in width (0/O width ratio below); 650 advance. -> ligated to an arrow. |
| Spline Sans Mono | dotted (small upright oval) | flag, full foot | flag, right tail | top bar, full foot | flag, full foot | double | double | none | Double-storey g. No box-drawing glyphs. |
| Anonymous Pro | slashed | flag, full foot | flag, full foot | top bar, full foot | flag, full foot | double | single | none | 546 advance; lightest (n stem 67). |
| Overpass Mono | dotted (round dot) | flag, full foot | flag, full foot | top bar, full foot | flag, full foot | double | single | 3 of 22: `->` `<-` `fi` | Bar | much taller than the brackets. Box lines present, block elements absent. -> ligated to an arrow. |
| Oxygen Mono | slashed | flag, full foot | flag, right tail | top bar, full foot | flag, full foot | double | single | none | Square period. No box-drawing glyphs. |
| Share Tech Mono | slashed | flag, full foot | flag, right tail | top bar, full foot | flag, right tail | double | double | 1 of 22: `fi` | 540 advance; squarish bowls (highest squareness of the set). No box-drawing glyphs. |
| PT Mono | slashed | flag, full foot | flag, right tail | top bar, full foot | flag, full foot | double | single | none | Partial box-drawing coverage (40 of 128). |
| Cousine | dotted (square dot) | flag, full foot | flag, full foot | top bar, full foot | flag, full foot | double | single | none | Metric-compatible with Courier New; l with a full foot. |
| Go Mono | slashed | flag, full foot | flag, right tail | top bar, full foot | flag, full foot | double | single | none | Slab serif with the strongest contrast (H bar / H stem 0.63). |
| Iosevka | slashed | flag, plain bottom | flag, full foot | top bar, full foot | flag, full foot | double | single | 15 of 22: `->` `=>` `!=` `<=` `>=` `==` `===` `::` ... | 500 advance; l with a full foot, 1 without a foot; uniform 78 stems and 70 horizontals. Ligatures on by default. |
| JuliaMono | dotted (diamond dot) | flag, full foot | flag, right tail | top bar, full foot | flag, full foot | double | double | 4 of 22: `->` `=>` `::` `|>` | Heavy operators (hyphen 100 thick against an 87.5 stem); arrows ligated by default; box verticals overshoot by about 250-275. |
| Fira Mono (dup) | dotted (round dot) | flag, full foot | flag, right tail | top bar, full foot | flag, full foot | double | double | none | Same outlines as Fira Code within 1 unit; no ligatures. |
| Cascadia Mono (dup) | dotted (large round dot) | flag, full foot | flag, right tail | top bar, full foot | flag, full foot | double | single | none | Cascadia Code without the ligatures. |
| Liberation Mono (dup) | dotted (square dot) | flag, full foot | flag, right tail | top bar, full foot | flag, full foot | double | single | none | Same metrics as Cousine; l with a right tail instead of a full foot. |
| Hack (dup) | long dot (tall upright ellipse, detached) | flag, full foot | flag, right tail | top bar, full foot | flag, right tail | double | single | none | DejaVu Sans Mono metrics and stems; differs in the zero and details. |
| Monaspace Neon (extra) | dotted (upright oval) | flag, full foot | flag, full foot | top bar, full foot | flag, full foot | double | single | 4 of 22: `!=` `//` `...` `||` | 620 advance. Default features change only !=, //, ..., || in the test list. |
| 0xProto (extra) | slashed | flag, full foot | flag, right tail | top bar, full foot | flag, full foot | double | double | 13 of 22: `->` `=>` `!=` `==` `===` `::` `|>` `<-` ... | f descends to -200; double-storey g; arrows ligated by default. Line height 1.56. |
| mononoki (extra) | slashed | flag, full foot | flag, right tail | top bar, full foot | flag, full foot | double | double | none | 562 advance; double-storey g. |
| B612 Mono (extra) | plain | flag, full foot | flag, right tail | top bar, full foot | flag, right tail | double | single | none | Plain zero; short = sign; 650 advance. No box-drawing glyphs. |

Reading the table: "flag" is a top-left serif; "full foot" a base serif on both sides; "right tail" a bottom that bends or extends to the right only. "fi" and "0x1F" in the shaping column are ordinary `liga` or contextual `x` substitutions rather than programming ligatures.

Counts over the core set: zero slashed 20 (one of them reversed), dotted 12, plain 2. `1`: flag in 34 of 34, with a foot in 30 and without in 4 (Roboto Mono, Inconsolata, Fragment Mono, Iosevka). `l`: top-left flag in 34, right tail 19, full foot 15. `I`: serifs top and bottom in 34. `i`: full foot 28, right tail 4, no foot 2. `a` is double-storey in 33; `g` is single-storey in 24 and double-storey in 10. Default shaping changes at least `->` in 10 of 34 and at least `!=` in 6.

## 6. What this means for our font

Recommended starting values for a 1000-unit em and a 600 advance, regular weight. Each row shows the reference data it rests on: the core median with its quartiles, and the median of the 600-advance subset. Where I depart from the median the comment says why. These are measurements of what existing fonts do, so they fix a defensible centre, not an optimum; the choices that go beyond the data are marked as inference below the table.

| group | parameter | recommended | core median (Q1 to Q3) | 600-subset median | n | comment |
|---|---|---:|---:|---:|---:|---|
| Em and heights | unitsPerEm | **1000** | – | – | – | 22 of 34 core designs use 1000, 8 use 2048, 4 use 2000 |
| Em and heights | advance | **600** | 600 (600 to 600) | 600 | 34 | 19 of 34 are exactly 600 |
| Em and heights | x-height | **530** | 522 (496 to 536) | 530 | 34 | the 600-subset median; x/cap = 0.752 |
| Em and heights | cap height | **705** | 700 (673 to 721) | 705 | 34 |  |
| Em and heights | ascender (l b d h k) | **745** | 730 (710 to 750) | 740 | 34 | cap height + 40 |
| Em and heights | ascender - cap height | **40** | 40 (20 to 51) | 41 | 34 | 8 designs use 0; the median keeps l taller than I |
| Em and heights | descender (p q y) | **-200** | -200 (-210 to -184) | -201 | 34 |  |
| Em and heights | descender of g | **-212** | -211 (-223 to -197) | -212 | 34 | round bottom: descender plus overshoot |
| Em and heights | figure height | **705** | 700 (673 to 722) | 710 | 34 | equal to the cap height, as in 26 of 34 |
| Em and heights | x-height / cap height | **0.752** | 0.745 (0.725 to 0.753) | 0.750 | 34 |  |
| Overshoot | o, n, e above x-height and below baseline | **11** | 11.0 (10.0 to 12.0) | 11.0 | 34 | 2.1% of the x-height |
| Overshoot | O, 0 above cap height and below baseline | **12** | 12.0 (10.4 to 14.0) | 12.0 | 34 | 1.7% of the cap height |
| Line | hhea ascender = typo ascender = winAscent | **955** | 957 (906 to 1004) | 984 | 34 | chosen so the cell centre equals the math axis |
| Line | hhea descender = typo descender = -winDescent | **-295** | -260 (-300 to -231) | -274 | 34 |  |
| Line | line gap (hhea and typo) | **0** | 0 (0 to 0) | 0 | 34 | 33 of 34 |
| Line | default line height | **1.250 em** | 1.200 (1.157 to 1.310) | 1.278 | 34 | between the core median and the 600-subset median |
| Line | cell aspect (height / width) | **2.083** | 2.063 (1.936 to 2.187) | 2.131 | 34 |  |
| Line | cell centre y | **330** | 350 (331 to 366) | 355 | 34 | (955 - 295) / 2 |
| Line | room above the caps | **250** | 250 (204 to 301) | 273 | 34 |  |
| Line | room below p | **95** | 62 (33 to 95) | 68 | 34 | at the upper quartile: the price of centring the cell on the operators |
| Stems | lowercase stem (n l i r) | **86** | 84.0 (78.5 to 90.0) | 85.8 | 34 | 0.162 of the x-height, 0.143 of the advance |
| Stems | capital stem (H I) | **88** | 86.8 (82.6 to 92.6) | 86.8 | 34 | n/H = 0.977 |
| Stems | m stems | **80** | 80.8 (75.2 to 83.2) | 82.0 | 34 | 0.93 of the n stem |
| Stems | o round side | **88** | 87.0 (83.1 to 90.2) | 88.5 | 34 | 1.023 of the n stem |
| Stems | O round side | **90** | 89.0 (84.4 to 94.6) | 89.7 | 34 | 1.023 of the H stem |
| Stems | o top and bottom | **74** | 73.0 (68.3 to 76.8) | 72.7 | 34 | 0.84 of the o side |
| Stems | O top and bottom | **77** | 75.8 (72.1 to 80.5) | 76.6 | 34 |  |
| Stems | H bar | **78** | 76.3 (70.2 to 81.5) | 76.3 | 34 | 0.886 of the H stem |
| Stems | e bar | **68** | 68.2 (64.2 to 72.0) | 68.2 | 34 | 0.79 of the n stem; the thinnest stroke |
| Stems | t bar | **70** | 69.8 (67.0 to 75.0) | 69.5 | 34 | top exactly on the x-height (median offset 0) |
| Stems | hyphen, plus, equal strokes | **76** | 75.8 (72.0 to 80.0) | 75.8 | 34 | 0.88 of the n stem |
| Stems | underscore thickness | **74** | 73.6 (69.2 to 77.8) | 73.6 | 34 |  |
| Spacing | n: lsb / rsb | **90 / 86** | 88 (80 to 96) | 90 | 34 | width 424 = 0.707 advance; counter 252 = 2.93 stems |
| Spacing | n counter | **252** | 250 (233 to 265) | 248 | 34 |  |
| Spacing | gap between n n / n counter | **0.70** | 0.712 (0.599 to 0.772) | 0.688 | 34 | 176 / 252 |
| Spacing | o: lsb = rsb | **64** | 64 (57 to 69) | 64 | 34 | width 472 = 0.787 advance; counter 296 |
| Spacing | H: lsb = rsb | **72** | 69 (62 to 79) | 69 | 34 | width 456 = 0.760 advance; counter 280 |
| Spacing | O: lsb = rsb | **48** | 47 (37 to 56) | 47 | 34 | width 504 = 0.840 advance |
| Spacing | 0 width / O width | **0.96** | 0.956 (0.917 to 0.995) | 0.962 | 34 | zero 484 wide, lsb 58 |
| Spacing | m: lsb = rsb | **46** | 48 (41 to 53) | 47 | 34 | width 508 = 0.847 advance; two counters of 134 |
| Spacing | m counter / n counter | **0.53** | 0.522 (0.493 to 0.546) | 0.523 | 34 |  |
| Spacing | w: lsb = rsb | **18** | 20 (12 to 30) | 16 | 34 | width 564 = 0.94 advance |
| Spacing | M: lsb = rsb | **54** | 52 (42 to 64) | 54 | 34 | width 492 = 0.82 advance |
| Spacing | W: lsb = rsb | **18** | 19 (9 to 32) | 18 | 34 | width 564 = 0.94 advance |
| Spacing | i: lsb / rsb | **92 / 72** | 92 (80 to 106) | 92 | 34 | flag left, foot both sides |
| Spacing | l: lsb / rsb | **72 / 68** | 74 (60 to 85) | 69 | 34 | flag left, tail right |
| Spacing | period: lsb = rsb | **226** | 226 (218 to 238) | 226 | 34 | 148 wide |
| Bowls | o outer squareness f | **0.735** | 0.731 (0.723 to 0.736) | 0.731 | 34 | superellipse exponent 2.25 |
| Bowls | o inner squareness f | **0.745** | 0.735 (0.728 to 0.749) | 0.741 | 34 | inner squarer than outer, as in 29 of 34 |
| Bowls | O outer squareness f | **0.745** | 0.738 (0.732 to 0.750) | 0.737 | 34 | capital squarer than lowercase, as in 28 of 34 |
| Bowls | 0 outer squareness f | **0.750** | 0.744 (0.735 to 0.751) | 0.745 | 34 |  |
| Punctuation | period diameter | **148** | 144 (130 to 156) | 148 | 34 | 1.72 stems; round |
| Punctuation | comma bottom | **-165** | -165 (-187 to -145) | -161 | 34 |  |
| Punctuation | colon lower dot centre | **66** | 64 (58 to 71) | 70 | 34 | same dot as the period |
| Punctuation | colon upper dot centre | **462** | 450 (431 to 462) | 458 | 34 | top 6 above the x-height |
| Punctuation | hyphen-minus width | **364** | 367 (310 to 401) | 361 | 34 | 0.607 advance |
| Punctuation | hyphen-minus centre y | **330** | 307 (276 to 329) | 303 | 34 | on the math axis (median offset 0) |
| Punctuation | underscore top / bottom | **-60 / -134** | -55 (-95 to -5) | -72 | 34 |  |
| Punctuation | underscore width / advance | **0.833** | 0.833 (0.771 to 1.000) | 0.812 | 34 | 500 wide; the median |
| Operators | math axis | **330** | 323 (302 to 346) | 325 | 34 | 0.623 of the x-height, 0.468 of the cap height |
| Operators | math axis / x-height | **0.623** | 0.620 (0.573 to 0.675) | 0.616 | 34 |  |
| Operators | plus width = height | **472** | 472 (447 to 489) | 473 | 34 | 0.787 advance |
| Operators | equal width | **460** | 460 (430 to 483) | 460 | 34 | 0.767 advance |
| Operators | equal gap | **128** | 129 (117 to 153) | 129 | 34 | 1.68 bar thicknesses |
| Operators | less / greater width | **436** | 434 (409 to 470) | 435 | 34 | 0.727 advance |
| Operators | less / greater height | **520** | 513 (485 to 566) | 545 | 34 |  |
| Operators | asterisk centre - math axis | **0** | 37 (2 to 171) | 58 | 34 | the data are split; a code font centres it |
| Brackets | [ ] { } ( ) top | **790** | 766 (710 to 819) | 766 | 34 | cap height + 85 |
| Brackets | [ ] { } ( ) bottom | **-130** | -145 (-164 to -121) | -150 | 34 | 70 above the descender |
| Brackets | bracket height | **920** | 915 (870 to 951) | 923 | 34 | centre 330 = math axis |
| Brackets | bracket centre - math axis | **0** | 1 (-24 to 23) | 0 | 34 |  |
| Brackets | bracket and bar stroke | **80** | 80.0 (75.8 to 89.3) | 84.2 | 34 |  |
| Brackets | bar | top / bottom | **790 / -130** | 762 (730 to 836) | 760 | 34 | same extent as the brackets |
| Lines | underline position (top of line) | **-100** | -100 (-109 to -75) | -100 | 34 |  |
| Lines | underline thickness | **50** | 50 (50 to 56) | 50 | 34 |  |
| Lines | strikeout position | **318** | 294 (259 to 317) | 300 | 34 | 0.60 of the x-height |
| Lines | strikeout size | **50** | 50 (50 to 51) | 50 | 34 |  |
| Box drawing | light line thickness | **80** | 79 (71 to 85) | 76 | 20 | 0.93 of the n stem |
| Box drawing | U+2500 centre y | **330** | 335 (305 to 350) | 344 | 20 | cell centre and math axis at once |
| Box drawing | U+2500 centre - cell centre | **0** | -2 (-38 to 3) | -2 | 20 |  |
| Box drawing | U+2500 overhang per side | **10** | 10 (4 to 24) | 10 | 20 | x from -10 to 610 |
| Box drawing | U+2502 beyond hhea ascender | **0** | 0 (0 to 80) | 0 | 20 | y from -295 to 955 |
| Box drawing | U+2502 beyond hhea descender | **0** | 37 (0 to 142) | 50 | 20 |  |
| Box drawing | U+2588 overhang | **0** | 0 (0 to 0) | 0 | 18 | 0..600 by -295..955 |

Further box-drawing ratios measured on the fonts that have the glyphs: heavy line U+2501 / light line U+2500 thickness, median 2.00 (Q1 2.00, Q3 2.00, n = 15); double line U+2550, each bar / light line 1.00 (Q1 1.00, Q3 1.00, n = 20) and gap / light line 1.00 (Q1 1.00, Q3 1.00, n = 20). Recommended: heavy = 2.0 x light = 160; double = two 80-unit bars with a 80-unit gap.

### Decisions the data support directly

1. **600 on 1000.** It is the modal cell (19 of 34), and it makes every number above comparable with JetBrains Mono, IBM Plex Mono, Source Code Pro, Fira Code, Commit Mono and Recursive without scaling.
2. **x-height 530, cap height 705, ascender 745, descender -200.** This is the centre of the 600-advance group: larger than Source Code Pro (486) and IBM Plex Mono (516), smaller than Commit Mono (540), DejaVu Sans Mono (547) and JetBrains Mono (550). Keep the ascender 40 above the caps: the median does, and it gives `l` and `I`, `b` and `6`, `d` and `0` a height difference for free.
3. **Lining figures at cap height.** 26 of 34 do it; the eight that do not differ by 18 units at most.
4. **One overshoot value per case: 11 lowercase, 12 capitals and figures,** equal at top and bottom. That is 2.1% of the x-height and 1.7% of the cap height, the medians.
5. **Stem 86 lowercase and 88 capitals; round sides +2%; horizontals at 0.84 to 0.89 of the vertical; e bar at 0.79.** A stem of 86 is 0.162 of the x-height, the median ratio (0.164), and sits between Source Code Pro (82), Fira Code and Commit Mono (84) and JetBrains Mono (90).
6. **Fit the m by thinning and squeezing, not by overflowing.** Stems at 0.93 of the n stem, counters at 0.53 of the n counter, sidebearings about half of the n's.
7. **Sidebearings from the table,** which reproduce the median rhythm: the gap between two n is 0.70 of the n counter. Round letters take about 0.71 of the straight sidebearing (o 64 against n 90), capitals less than lowercase (H 72, O 48).
8. **Zero narrower than O (0.96) and marked.** 31 of 34 mark the zero (19 slashed, 12 dotted); the three that do not are a typewriter face and two display-leaning designs. The measurements do not choose between slash and dot; they do show that a slash kept inside the counter (Commit Mono, Fira Code, Iosevka) is the majority form.
9. **`1` with flag and foot, `l` with a top-left flag and a right tail, `I` with two serifs, `i` with a flag and a full foot.** These are the majority forms (30, 19, 34 and 28 of 34). The three glyphs then differ at the bottom: foot on both sides, tail to the right, serif on both sides plus a serif on top.
10. **One operator axis at y = 330** for `+ - = < >`, the brackets, braces, parentheses and the bar, and the same value for the centre of the line box. In the reference fonts the four operators agree with each other (median spread 1 unit), the hyphen-minus sits on their axis (median offset 0) and so do the brackets (median offset 1), but the axis and the cell centre differ by a median of 30 units and the box-drawing line follows the cell centre, not the axis (median offsets -2 and +8). Cascadia Code is the one callout font where all three coincide (0, -2, -1). Choosing ascender 955 and descender -295 puts the centre of a 1.25 line at 330, so `->`, `|`, `[`, `─` and `│` line up without any glyph being moved off its natural position.
11. **Line height 1.25 with hhea = typo = win and no line gap, USE_TYPO_METRICS set.** The reference range is 1.10 (Commit Mono) to 1.38 (Intel One Mono); the core median is 1.20 and the 600-subset median 1.28. Identical values in all three tables remove the platform differences measured in section 4.3 (Source Code Pro 1.257 against 1.514, Fira Code 1.312 against 1.582).
12. **Box drawing: light line 80 thick, exactly the height of the line box, 10 units of horizontal overhang, block elements exactly on the cell.** Eight of the 20 core fonts with U+2502 fit the hhea box exactly, and that is the only choice that keeps winAscent and winDescent equal to the hhea values. Ship the full 128 box-drawing and 32 block-element code points: 14 of 34 core fonts have none, and a TUI user is the one who notices.

### Inference, not measurement

- **Squareness.** The median bowl is nearly elliptical (f = 0.731, exponent 2.21). I recommend 0.735 for the o and 0.745 for the O, half a step toward the square, and keeping the two regularities the data show (inner squarer than outer, capitals squarer than lowercase). Whether to go as far as JetBrains Mono (0.770 and 0.806) is a design decision the measurements cannot make; expose it as one parameter.
- **Asterisk on the axis.** 13 of 34 centre it within 12 units and 10 raise it by more than 100. For `a * b`, `**kwargs` and `*args` the centred form reads as an operator; I recommend it and it should be tested in real code.
- **Underscore 500 wide.** The median leaves a gap between consecutive underscores (0.833 of the advance); 10 of 34 make them join. A visible gap lets `__init__` be counted; that is my reasoning, not a measured effect.
- **Colon.** The reference colon is a text colon: centred 61 below the math axis. I recommend the same default (lower dot 66, upper dot 462) and a contextual or stylistic alternate that raises it to the axis for `::` and `:=`, as an experiment.
- **Box-drawing overshoot.** Commit Mono, JuliaMono and Victor Mono let verticals run 175 to 300 units past the line box so that they still meet when the user increases line spacing. The exact fit recommended here assumes the default line spacing or a terminal that draws these glyphs itself; which terminals do is outside what I measured.

### Checks to run on our own font

The measuring code in `research/rm/` takes any font file. Run it on each build and compare with this table; in particular: x-height equals OS/2 sxHeight; `+ - = < >`, brackets and U+2500 centres all within 2 units of 330; U+2502 bbox equals (hhea descender, hhea ascender); every ASCII advance equals 600; stem ratios within the quartiles above.

## 7. Gaps and limits

- Regular weight and upright only. Nothing here says how these numbers move with weight or in the italic.
- The statistics describe what designers did, not what reads best; no legibility measurement is implied.
- Vertical stems are taken at one scan height per glyph; tapered or flared stems (Space Mono, Go Mono) are represented by that one value.
- The t-bar and e-bar values assume a horizontal bar; none of the fonts measured has a slanted one.
- Squareness is one number per contour (the diagonal crossing); it does not describe where along the curve the tension sits.
- Commercial coding fonts (Berkeley Mono, MonoLisa, Operator Mono, PragmataPro, Input) were not measured.
- How terminals and editors choose between hhea, typo and win metrics, and which of them draw box-drawing glyphs themselves, was not tested here.
- Hinting and rendering at small pixel sizes were not examined; all values are from unhinted outlines.

## 8. Files

- `/tmp/claude-0/-home-user-experiments/a86123d7-7ed9-5f3d-9952-1d096afee651/scratchpad/research/ref_metrics.md`: this report.
- `/tmp/claude-0/-home-user-experiments/a86123d7-7ed9-5f3d-9952-1d096afee651/scratchpad/research/ref_metrics.json`: one object per font with every number.
- `/tmp/claude-0/-home-user-experiments/a86123d7-7ed9-5f3d-9952-1d096afee651/scratchpad/research/contact-*.png`: contact sheets (ten groups, three enlargements, one sheet of zeros).
- `/tmp/claude-0/-home-user-experiments/a86123d7-7ed9-5f3d-9952-1d096afee651/scratchpad/research/rm/`: `fonts.py` (registry and instancing), `geom.py` (flattening and scan lines), `measure.py`, `verify.py`, `stats.py`, `sheets.py`, `report.py`, `recommend_build.py`; `verify.json`; `manifest.json` (google/fonts paths and upstream commits); `src/` (specification pages quoted above).
- `/tmp/claude-0/-home-user-experiments/a86123d7-7ed9-5f3d-9952-1d096afee651/scratchpad/refs/`: the font files. `/tmp/claude-0/-home-user-experiments/a86123d7-7ed9-5f3d-9952-1d096afee651/scratchpad/research/rm/inst/`: the wght=400 instances. `/tmp/claude-0/-home-user-experiments/a86123d7-7ed9-5f3d-9952-1d096afee651/scratchpad/research/venv-rm/`: the Python environment.
