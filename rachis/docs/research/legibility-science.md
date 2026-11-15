# Legibility science for a screen monospace: what the evidence sets, and what it does not

Research date: 2026-11-14. Scope: peer-reviewed and standards evidence that should fix parameters of a monospaced typeface for code, plain-text mathematics and terminal UIs, read at 12–14 px.

**How to read this report.** Every claim carries a link to the source I actually read. Each is tagged:

- **[P]** primary source read in full text;
- **[A]** primary source, abstract only (the authors' own abstract, usually via PubMed);
- **[S]** secondary source reporting a primary one I could not open;
- **[M]** measured or computed by me in this session (scripts listed in the appendix);
- **[I]** my inference.

Three full texts tagged [P] were read through a fetch-and-extract tool rather than line by line: Kremkow et al. 2014, Grissinger 2017 and UTS #39. Their quoted numbers are the tool's extraction and deserve a second look before they carry weight.

Numbers are quoted with the units the source uses. "x-height" always means the height of a lowercase x; angles are visual angles.

---

## 0. The operating point: where 12–14 px code text sits

This is computed first because every later section depends on it.

Legge and Bigelow define print size as angular x-height and give the conversion "angular size = 57.3 × physical size / viewing distance" [[P]](https://pmc.ncbi.nlm.nih.gov/articles/PMC3428264/). Applying it to a monospace with a 0.60 em advance [M]:

| CSS px/inch | distance | 12 px, x-height 0.53 em | 14 px, x-height 0.53 em | 14 px advance (centre-to-centre) | 1 CSS px |
|---|---|---|---|---|---|
| 96 | 50 cm | 0.193° | 0.225° | 0.255° | 1.82′ |
| 96 | 60 cm | 0.161° | 0.187° | 0.212° | 1.52′ |
| 96 | 70 cm | 0.138° | 0.161° | 0.182° | 1.30′ |
| 109 (27″ QHD) | 60 cm | 0.142° | 0.165° | 0.187° | 1.34′ |
| 127 (254 ppi laptop at 2×) | 50 cm | 0.146° | 0.170° | 0.193° | 1.38′ |
| 127 | 60 cm | 0.121° | 0.142° | 0.160° | 1.15′ |

Viewing distances: Legge and Bigelow cite a study of preferred reading distances that "found a mean close to 50 cm for both electronic paper and video display terminals" [[P]](https://pmc.ncbi.nlm.nih.gov/articles/PMC3428264/); the German federation of the blind's DIN 1450 guidance assumes a desktop monitor "etwa 70 Zentimeter entfernt" [[S]](https://leserlich.info/zeichen/schriftgroesse).

**Result [M, I].** In every cell of the table but one (14 px at 96 ppi and 50 cm), 12–14 px code has an x-height of 0.12°–0.19°, which is at or below the 0.2° critical print size (section a). To reach 0.20° at 96 ppi and 60 cm a font with x-height 0.53 em needs 14.9 px; at 109 ppi and 70 cm it needs 19.8 px. A code font is therefore read as *small print near the critical print size*, and the evidence about small print is the evidence that applies.

---

## (a) x-height, letter size and critical print size

**The fluent range and the critical print size.** "The fluent range extends over a factor of 10 in angular print size (x-height) from approximately 0.2° to 2°." The critical print size (CPS), below which reading speed "begins to decline sharply", "typically lies in the range from about 0.15° to 0.3°", and "a consensus value for the critical print size for normally sighted readers is 0.2° x-height"; one RSVP study measured a mean of 0.17° (range 0.14°–0.24°) [[P] Legge & Bigelow 2011](https://pmc.ncbi.nlm.nih.gov/articles/PMC3428264/). Reading below CPS "slows but does not stop" (same source).

**Print sits just above CPS.** Newspaper running text averages 0.23° x-height (range 0.20°–0.26°); hardcover and paperback novels 0.24° [[P]](https://pmc.ncbi.nlm.nih.gov/articles/PMC3428264/). On-screen news article text (132 ppi, 40 cm) averaged 7.53 px x-height = 0.21°, home-page text 6.78 px = 0.19° (same source, Table 6).

**x-height fraction.** Across 1049 roman typefaces the x-height fraction ranges 0.28–0.58, mean 0.46. By use: hardcover book faces 0.42 (SD 0.04), newspaper faces 0.48 (SD 0.03), print faces adapted to screens 0.49 (SD 0.04), "digital typefaces designed for screens" 0.52 (SD 0.03) [[P]](https://pmc.ncbi.nlm.nih.gov/articles/PMC3428264/). Legge and Bigelow say explicitly that the claim that x-height drives perceived size rests on typographic opinion, not laboratory studies.

**Larger x-height fraction and more pixels help on screens.** In a threshold-legibility study of 6 fonts, "Verdana and Arial were the most legible fonts; Times New Roman and Franklin were least legible" [[A] Sheedy et al. 2005](https://pubmed.ncbi.nlm.nih.gov/16553067/); Legge and Bigelow give the x-height fractions as Verdana 0.55, Arial 0.52, Georgia 0.48, Times New Roman 0.45, and report that at equal angular size "legibility was greater when fonts were rendered with more pixels" [[P]](https://pmc.ncbi.nlm.nih.gov/articles/PMC3428264/).

**How few pixels suffice.** Reading rate increases with sample density only up to a critical value, "about 4 × 4 samples/character for 0.1 degree characters to more than 20 × 20 samples/character for 24 degrees characters" [[A] Legge et al. 1985](https://pubmed.ncbi.nlm.nih.gov/4013091/). A 12 px monospace gives about 7 × 6.4 px for an x-height letter, above that floor [M].

**Which spatial frequencies carry small letters.** Low-pass filtered text is read at full speed down to a cutoff of "two cycles/character" [[A] Legge et al. 1985](https://pubmed.ncbi.nlm.nih.gov/4013091/); a later study put the critical cutoff for reading speed, visual span and letter recognition "all near 1.4 CPL" [[A] Kwon & Legge 2012](https://pubmed.ncbi.nlm.nih.gov/22521659/). For 1° letters the tuning peak is 3 cycles per letter, and for a print size of 0.16° the estimated peak is 1.7 cycles per letter: "Identification of letters near the critical print size depends on coarser features" [[P] Legge & Bigelow 2011](https://pmc.ncbi.nlm.nih.gov/articles/PMC3428264/). Majaj et al. found a single channel 1.6 ± 0.7 octaves wide whose centre frequency follows stroke frequency with log-log slope 2/3, so that "small letters … are identified by their gross strokes" [[A] Majaj et al. 2002](https://pubmed.ncbi.nlm.nih.gov/11997055/).

**Optical scale.** Legge and Bigelow connect this to type-founders' practice: a caption-size design has "a bigger x-height, greater width, thicker details, and looser spacing"; in Arno Pro the 8.5 pt design's x-height is 6% greater and its mean lowercase width 15% greater than the 22 pt design's [[P]](https://pmc.ncbi.nlm.nih.gov/articles/PMC3428264/).

**Standards.** DIN 1450 specifies size by x-height as a visual angle. DIN's own page marks the 2013-04 edition "[Withdrawn]" [[P]](https://www.din.de/en/getting-involved/standards-committees/natg/publications/wdc-beuth:din21:170093157); the edition DBSV cites is November 2024 [[S]](https://leserlich.info/zeichen/strichstaerke). The standard is paywalled; the German federation of the blind (DBSV) reproduces it. Its calculator, which states it follows DIN 1450, uses minimum x-heights of 13′ for reading text (Lesetext), 10′ for consultation text, 20′ for display text and 9′ for signage, multiplied by (lighting factor: good 0.7, medium 0.85, poor 1.0) ÷ visual acuity, with defaults acuity 0.7 and x-height/size 0.47 [[S, read from the calculator's form values and script]](https://leserlich.info/schriftgroessenrechner). A German federal accessibility guide gives the resulting desktop sizes as "22px für Textblöcke, 17px für nebensächlichen Text" [[S]](https://handreichungen.bfit-bund.de/bfit-leitfaeden/6.0/pdf/bfmb_barrierefreie-textgestaltung-uie.pdf); I reproduced 22.2 px and 17.1 px from 13′ and 10′ at 70 cm, 100 ppi [M]. A 14 px code font with x-height 0.54 em at 70 cm and 100 ppi subtends 9.4′, below DIN's consultation-text minimum [M].

---

## (b) Letter spacing, crowding, and whether monospace's width helps

**Crowding, not acuity, sets the critical print size.** "Well-corrected fluent observers reading ordinary text with adequate light are limited by letter spacing (crowding), not size (acuity)"; reading rate is proportional to the uncrowded span, and this holds "provided only that text contrast is at least four times the threshold contrast for an isolated letter" [[A] Pelli et al. 2007](https://pubmed.ncbi.nlm.nih.gov/18217835/). The Bouma law is S = S₀ + bΦ, with S₀, the critical centre-to-centre spacing near fixation, "roughly 0.1° to 0.2°"; "the critical print size for reading is not a consequence of the size of the letters per se, but a result of the center-to-center spacing between adjacent letters falling within the critical spacing for crowding" [[P] Legge & Bigelow 2011](https://pmc.ncbi.nlm.nih.gov/articles/PMC3428264/).

[M, I] At 12–14 px a 0.60 em advance is 0.16°–0.25° centre to centre (table in section 0): inside or at the edge of S₀. The advance width, not the glyph height, is the binding constraint.

**More spacing than standard does not help; less hurts.** In Courier, "reading speed increased with letter spacing, up to a critical letter spacing, and then either remained constant … or decreased slightly"; the critical spacing "was very close to the standard letter spacing" (standard Courier spacing = 1.16 × the width of a lowercase x) at the fovea, 5° and 10°, and for print 0.8× and 1.5× CPS [[A] Chung 2002](https://pubmed.ncbi.nlm.nih.gov/11923275/). Yu et al. tested 0.5×, 0.707×, 1× and 2× standard at x-heights of 0.08° and 0.15° (10 and 18 px): the visual span was largest at standard spacing (37.4 ± 4.5 bits small print, 45.5 ± 2.4 bits large print) and fell at 2×; spacing had a "greater impact … near the acuity limit" [[P] Yu et al. 2007](https://pmc.ncbi.nlm.nih.gov/articles/PMC2729067/).

[M] Reference monospaces sit on that optimum: advance ÷ x-width is 1.20 (JetBrains Mono), 1.14 (DejaVu Sans Mono), 1.18 (Liberation Mono), 1.20 (FreeMono).

**Fixed pitch versus proportional.**

- Same letterforms, pitch varied: variable pitch gave "better performance at medium and large character sizes and fixed pitch [was] superior for character sizes approaching the acuity limit"; the advantage of variable pitch came from "greater horizontal compression and consequently reduced eye-movement requirements" [[A] Arditi et al. 1990](https://pubmed.ncbi.nlm.nih.gov/2231111/).
- Courier-Bold versus Times-Roman, matched for x-height, 50 normal and 42 low-vision subjects: reading acuity better with Courier by 0.05 logMAR (normal; a 12% size difference) and 0.09 logMAR (low vision); CPS smaller by 0.06 logMAR (15%); maximum reading speed of normal subjects 4.7% faster with Times; low-vision subjects 10% slower with Times; below CPS, speeds "substantially slower (by as much as 50%) for Times". Courier's mean character width is 40% wider at equal x-height. The authors caution that stroke thickness and serifs also differ [[P] Mansfield et al. 1996](https://legge.dl8.umn.edu/sites/legge.psych.umn.edu/files/files/media/mansfield96_psychophysics_of_reading_xv-_font_effects_in_normal_and_low_vision.pdf).
- Consolas versus Georgia, eye tracking, 32 readers: "the type of font did not influence reading rate"; Consolas "yielded more forward fixations … but fixation durations were shorter", and the perceptual span did not differ [[P] Rayner et al. 2010](https://pmc.ncbi.nlm.nih.gov/articles/PMC3075059/).
- Macular degeneration, 24 patients, four fonts: reading acuity best with Courier (0.58 ± 0.21 logMAR) and worst with Arial (0.69 ± 0.20); no difference in maximum speed; "Courier was the most advantageous … This is contrary to the advice given by agencies for the blind" [[A] Tarita-Nistor et al. 2013](https://pubmed.ncbi.nlm.nih.gov/23419299/).
- Five fonts, 19 MD and 40 normal subjects: two fonts designed for MD "presented no advantage over Courier". With Spacing defined as centre-to-centre separation ÷ x-height (range 0.92–1.50 across fonts), "an increase in Spacing was associated with slower MRS, but better CPS and RA"; across that range reading acuity changed by 0.12 logMAR in young controls and maximum speed by 19% in the MD group. Narrowing one font from Spacing 1.24 to 0.98 gave the MD group faster maximum speed but larger CPS and worse acuity [[P] Xiong et al. 2018](https://pmc.ncbi.nlm.nih.gov/articles/PMC6100668/).
- Proofreading: no significant difference between monospaced typewriter faces and proportional typefaces; an irregularly spaced face reduced accuracy [[A] Black & Watts 1993](https://journals.uc.edu/index.php/vl/article/view/5586).

**Letter width.** Wider letters were recognised better and misread less in trigrams at 2° and 9° eccentricity (Helvetica Neue Condensed, Standard, Extended) [[A] Oderkerk & Beier 2022](https://pubmed.ncbi.nlm.nih.gov/34704915/); in continuous reading across four Univers widths "no reading-speed differences were observed" because eye movements adapted [[A] Minakata & Beier 2021](https://pubmed.ncbi.nlm.nih.gov/34225106/).

**Answer.** Monospace's wide, even spacing costs at most about 5% of maximum prose reading speed at comfortable sizes and buys roughly 0.05 logMAR of reading acuity and 0.06 logMAR of critical print size. Code is read near CPS, so the trade is favourable. Spacing wider than the Courier standard buys nothing.

---

## (c) Stroke weight and contrast polarity

**Stroke weight.** Courier at six boldness levels (0.27, 0.72, 1, 1.48, 1.89, 3.04 × standard stroke width), print at 0.8× and 1.4× CPS: "At the fovea, reading speed was invariant for the middle four levels of boldness, but dropped by 23.3% for the least and the most bold text"; at 10° eccentricity speed fell 21.5% at 1.89× and 51% at 3.04×. "reading speed does not benefit from bold text in the normal fovea and periphery." Standard stroke width ÷ x-height is 0.165 for Courier, 0.151 for Arial, 0.124 for Times New Roman. The invariant band is therefore 0.119–0.312 of x-height. The authors attribute the loss at 3.04× to closing counters and shrinking edge-to-edge gaps (equivalent to 0.72× standard spacing), and the loss at 0.27× to low RMS contrast [[P] Bernard et al. 2013](https://pmc.ncbi.nlm.nih.gov/articles/PMC3642228/).

On screens, "increased stroke width (bold) improved threshold legibility but only at the thinnest width tested" [[A] Sheedy et al. 2005](https://pubmed.ncbi.nlm.nih.gov/16553067/).

**Stroke contrast.** In bold fonts, the high-stroke-contrast design impaired letter recognition relative to low and medium contrast, which did not differ [[A] Beier & Oderkerk 2021](https://pubmed.ncbi.nlm.nih.gov/34174575/).

**DIN 1450 (2024 edition, via DBSV) [S].** Stem thickness 10–20% of x-height for reading text, 13–20% for consultation text; 17–20% for signage text, with hairlines not below 12% of x-height [(source)](https://leserlich.info/zeichen/strichstaerke). Typeface width: the inner distance between the stems of n is about 50% of the x-height at normal width [(source)](https://leserlich.info/zeichen/schriftweite). Letter spacing, measured stem to stem between adjacent letters, for sans serifs: 67–72% of that n-width for reading text, 70–75% for consultation text, 73–78% for signage; "Die in der DIN 1450 empfohlenen Zeichenabstände wurden im Jahr 2024 korrigiert" [(source)](https://leserlich.info/zeichen/zeichenabstand).

[M] Reference fonts against those numbers (rendered at 14 px/em, 16× supersampled):

| font | x-height/em | stem/x-height | stem (per 1000 em) | stem:horizontal | n counter/x-height | n-to-n gap ÷ n counter | advance/x-height |
|---|---|---|---|---|---|---|---|
| JetBrains Mono Regular | 0.549 | 0.163 | 89 | 1.11 | 0.43 | 0.77 | 1.09 |
| DejaVu Sans Mono | 0.549 | 0.163 | 89 | 1.25 | 0.44 | 0.76 | 1.10 |
| Liberation Mono | 0.527 | 0.169 | 89 | 1.33 | 0.47 | 0.71 | 1.14 |
| FreeMono (Courier-like) | 0.415 | 0.102 | 42 | 1.06 | 0.66 | 0.89 | 1.45 |

The three screen monospaces converge on a stem of 16–17% of x-height, the same ratio Bernard et al. report for Courier and the centre of the performance plateau.

**Polarity.**

- Dark-on-light gave better proofreading than light-on-dark regardless of ambient light and chromaticity [[A] Buchner & Baumgartner 2007](https://pubmed.ncbi.nlm.nih.gov/17510822/), for younger and older adults [[A] Piepenbrock et al. 2013](https://pubmed.ncbi.nlm.nih.gov/23654206/).
- "The positive polarity advantage linearly increased with decreasing character size" over 8, 10, 12, 14 pt (0.22°, 0.25°, 0.31°, 0.34° vertical angle); "especially with small font sizes, negative polarity displays should be avoided" [[A] Piepenbrock et al. 2014](https://pubmed.ncbi.nlm.nih.gov/25141597/). [M] A 12–14 px code font at 96 ppi and 60 cm has a cap height of about 0.22°–0.26°: the small end of that range.
- The cause is luminance, not polarity: "No positive polarity advantage was observed when overall display luminance of positive and negative polarity displays was equivalent" [[A] Buchner et al. 2009](https://pubmed.ncbi.nlm.nih.gov/19562598/). The proposed mechanism is pupil constriction reducing optical aberrations; glance-legibility thresholds were worst for negative polarity in dark surroundings and equalised under daylight-like illumination [[A] Dobres et al. 2017](https://pubmed.ncbi.nlm.nih.gov/28166901/).
- Size of the effect in glance reading: positive polarity thresholds were "38.6% lower than negative polarity"; in negative polarity, reducing cap height from 4 mm to 3 mm (13 to 10 px) raised thresholds 26.4% for a humanist sans and 62.1% for a square grotesque, whose "i" and "j" "lose identifying characteristics at the smaller size" [[P] Dobres et al. 2016](https://pmc.ncbi.nlm.nih.gov/articles/PMC5213401/).
- Older work on a TV monitor found "contrast polarity … has no effect" on reading rate [[A] Legge et al. 1985](https://pubmed.ncbi.nlm.nih.gov/4013091/), and similar results for both polarities across contrasts [[A] Legge et al. 1987](https://pubmed.ncbi.nlm.nih.gov/3660667/). This is consistent with Buchner et al. if luminance was comparable.

**Irradiation.** "A light patch on a dark background appears larger than the same sized dark patch on a light background"; the neural basis is a saturating ON pathway. ON/OFF receptive-field centre size ratio was 1.47 in LGN and 1.29 in V1 on dark backgrounds, and 0.99 and 0.8 on grey backgrounds [[P] Kremkow et al. 2014](https://pmc.ncbi.nlm.nih.gov/articles/PMC3939872/). [I] Light strokes on a dark ground therefore look heavier and counters look smaller, most strongly on true-black backgrounds.

**DIN 1450 for light-on-dark [S].** Increase size by 10% [(source)](https://leserlich.info/zeichen/schriftgroesse) and letter spacing by about 2% [(source)](https://leserlich.info/zeichen/zeichenabstand).

I found no peer-reviewed measurement of the optimal stroke weight for light-on-dark text.

---

## (d) Letter and digit confusion

### What the confusion matrices say

**Uppercase.** Mueller and Weidemann ran two 2-AFC experiments on all 650 ordered pairs of uppercase letters in 16-pt Courier New Bold (118 and 96 participants, mean exposure 54 ms). Lowest accuracies: Q→O .347, C→O .508, D→Q .542 with an "@" mask; with a "#" mask I→V .379, X→K .466, Q→O .483, T→F .483. They reviewed more than 50 earlier studies; eleven uppercase studies intercorrelated at .26–.81 (mean .42). Their model separates perceivability, bias and similarity: ln(p/(1−p)) ∝ μ + λᵢ + γᵢ − γⱼ + δᵢⱼ. Perceivability and bias depended on the mask; "round characters were generally found to be similar across experiments" [[P] Mueller & Weidemann 2012](https://pmc.ncbi.nlm.nih.gov/articles/PMC3271710/).

**Lowercase.** Bouma, with Courier-style lowercase at distance and in eccentric vision: "Dominating similarities are /h k b/, /t i l f r/, /e o c/, /a s z x e/, /v w/ and /g q/. Properties with high cue values are: (1) vertically ascending and descending parts, (2) slenderness, (3) outer vertical and outer oblique parts, and also outer gaps. Inner parts are weak cues at best" [[A] Bouma 1971](https://research.tue.nl/en/publications/visual-recognition-of-isolated-lower-case-letters/). Beier and Larson summarise Geyer, Bouma and Tinker as two high-error groups: x-height letters built from straight and curved strokes (e, c, a, s, n, u, o) and narrow single-stem letters (i, j, l, t, f) [[P]](https://www.microsoft.com/en-us/research/uploads/prod/2021/06/Beier-Larson-2010-Design-Improvements-for-Frequently-Misrecognized-Letters.pdf).

**Features.** "Line terminations are the most important features for letter identification" (Bubbles technique, Arial upper and lower case) [[A] Fiset et al. 2008](https://pubmed.ncbi.nlm.nih.gov/19076489/).

**Letters, digits and symbols together.** Ten participants, 47 characters (a–z, 0–9, eleven symbols), 20 typefaces, 10 pt, 34 ms exposure. Verdana 97% correct, Garamond 93%. In Verdana "the letter 'i' was confused most often with the letter 'j'"; in Garamond "the number '0' was confused with the letter 'o', the '#' sign was confused with the '=' sign, the number '1' was confused with the letter 'l', and the letter 'e' was confused with the letter 'c'". Classification trees: for "e", a crossbar position below .61 of the height gave 92% correct against 10% above it; "short zeroes were confused more often than tall zeroes (24% versus 89% correct identification)", and short zeros remained legible when their perimetric complexity was high [[P] Merkle & Chaparro 2009](https://csbigs.fr/index.php/csbigs/article/view/337.html).

**Alphanumeric errors in practice.** "The symbols 'l' and '1,' 'O' and '0,' 'Z' and '2,' and '1' and '7' accounted for more than half of the errors caused by symbol misidentification" in a Bell Laboratories study. The article's table also lists b/6, g/9, q/9, I/l, D/O, B/8, S/5, G/6, and among digits 0/8, 3/9, 3/8, 4/9, 5/8, 5/3, 6/8, 7/1 [[S] Grissinger 2017](https://pmc.ncbi.nlm.nih.gov/articles/PMC5614409/).

**Unicode's list.** UTS #39 (version 18.0.0, 2026-08-27) defines confusability by a skeleton: "X and Y are … confusable if and only if skeleton(X) = skeleton(Y)". The data came from "running a program over a large number of fonts" to catch identical glyphs, plus contributed lists, and "confusability among characters cannot be an exact science" [[P]](https://www.unicode.org/reports/tr39/). [M] Parsing the current [confusables.txt](https://www.unicode.org/Public/security/latest/confusables.txt) (dated 2026-08-06) for mappings with ASCII on both sides gives exactly seven: `` ` ``→`'`, `"`→`''`, `|`→`l`, `1`→`l`, `I`→`l`, `0`→`O`, `m`→`rn`.

### Which design changes are tested

Beier and Larson built three test fonts with variants of the frequently misread letters and tested them at distance and in 43 ms parafoveal exposure (41 participants) [[P]](https://www.microsoft.com/en-us/research/uploads/prod/2021/06/Beier-Larson-2010-Design-Improvements-for-Frequently-Misrecognized-Letters.pdf):

- "We recommend wide versions of narrow letters. The wide j2, l2, and t2 all showed versions that performed better than their more narrow forms." The tailed l was better than the serifed and the plain-stem forms; narrow l was misread as i and t. A broad t "introduces a new confusion with the letter 'c'".
- "The hypothesis that a single storey 'a' is less legible than the double storey 'a' was confirmed. With a high level of misreadings for 'o' and 'q', we recommend against the single storey 'a'."
- A slab serif on top of i helped at distance (reliably in one font); a serif at the bottom made it harder to identify.
- Extending letters into the ascender and descender zones helped (an ascending a, a descending s, a descending f).
- Not confirmed: differentiating u from n (a tailless u was no better and once worse); opening the aperture of c. "The extremely closed e4 versions performed worse than the more open" versions, so only extreme closure of e hurt.
- A t shaped like a small capital T was misread as r.

Numerals in crowded three-digit strings in peripheral vision: "the digit '1' should have a narrow design without a crossbar at the bottom, the digits '3' and '9' should benefit from open apertures, and the digit '7' should have a straight leg and no serif at the horizontal bar"; "crowded digits … generally profit from a short morphological skeleton" [[A] Beier et al. 2018](https://adk.elsevierpure.com/en/publications/numeral-legibility-and-visual-complexity/).

DIN guidance: DIN 1451-1's press release recommends humanist sans serifs for their "deutlicher unterscheidbarere (I, l, a, q, g) und offenere Buchstabenformen (a, e, s)" and low stroke contrast [[P] DIN press release](https://www.din.de/resource/blob/317896/df49e6201e9bba01e38d8bd6bfcebeb2/leserlichkeit-schriften-data.pdf). DBSV on DIN 1450: "Verwechselbare Zeichenformen finden sich auch bei 1, I und l sowie bei O und 0"; openness matters most for a, c, e, o, s [[S]](https://leserlich.info/zeichen/schriftart).

### What three reference monospaces actually do [M]

Blurred-template distance D (defined in section f) at 14 px/em with a visual blur of σ = 1.0 px. D = 0 means identical, 1.41 means no overlap. The median over all 1891 alphanumeric pairs is 0.62–0.66.

| pair | JetBrains Mono | DejaVu Sans Mono | Liberation Mono | FreeMono |
|---|---|---|---|---|
| 8 B | 0.11 | 0.14 | 0.17 | 0.27 |
| D O | 0.12 | 0.18 | 0.15 | 0.27 |
| 0 O | 0.14 | 0.21 | 0.22 | 0.31 |
| 5 S | 0.15 | 0.19 | 0.17 | 0.33 |
| 0 8 | 0.17 | 0.18 | 0.17 | — |
| 1 I | 0.25 | 0.25 | 0.28 | 0.22 |
| 1 l | 0.45 | 0.47 | 0.43 | 0.20 |
| l I | 0.44 | 0.45 | 0.41 | 0.24 |
| g q | 0.25 | 0.27 | 0.28 | 0.29 |
| h b | 0.25 | 0.27 | 0.24 | 0.25 |
| n h | 0.27 | 0.30 | 0.30 | 0.31 |
| e o | 0.26 | 0.29 | 0.29 | 0.38 |
| c o | 0.29 | 0.52 | 0.35 | 0.27 |
| . , | 0.57 | 0.57 | 0.77 | 0.72 |
| ( { | 0.41 | 0.30 | 0.33 | 0.56 |

Two observations. First, the pairs this metric ranks worst (8/B, D/O, 0/O, 5/S, 0/8) are the same pairs Grissinger's table and Unicode list. Second, all three screen fonts mark their zero (ink at its centre), yet 0/O stays at 0.14–0.22 because the outlines nearly coincide (JetBrains Mono: zero 440 × 750 units, O 424 × 750). FreeMono's unmarked zero scores 0.31 because it is 374 units wide against 498 for O. Under blur, outline width separates 0 from O better than an inner mark does. This agrees with Bouma's "inner parts are weak cues at best".

---

## (e) Empirical studies of fonts for programming

**The evidence is thin. I found no peer-reviewed controlled experiment that compares typefaces, monospaced against proportional fonts, or ligatures, for reading source code.**

- A systematic review of formatting and code legibility screened 4,914 documents and kept 15 papers with 13 factors: indentation, spacing, block delimiters, line length, statements per line, identifier style. It states: "we did not consider studies that investigate the influence of typography, colors, contrast, or dynamic presentation". It calls the area "immature" and notes 5 of 15 papers are 30 or more years old [[P] Oliveira et al. 2023](https://arxiv.org/abs/2208.12141).
- A position paper lists typefaces and anti-aliasing among untested factors: "Among developers monospace seems to be a foregone conclusion"; "much current practice lacks validation" [[P] Jacques & Kristensson 2015](https://pokristensson.com/pubs/JacquesKristenssonPLATEAU2015.pdf).
- Four web searches and two arXiv index searches for a ligature or typeface study on code returned only opinion pieces, vendor claims and the two papers above.
- Nearest evidence, on identifier style: 15 students "took 13.5% longer for camel-cased identifiers than underscored" (p = 0.0001) with no accuracy difference, while a later study found camel case better in one experiment and no difference in another [[S] via Oliveira et al. 2023](https://arxiv.org/abs/2208.12141). This bears on how visible the underscore must be, and nothing more.
- General reading: across 16 fonts with size normalised, each person's fastest font was read 35% faster than their slowest, "one font does not fit all", and "preference does not predict speed" [[P] Wallace et al. 2022](https://jeffhuang.com/papers/Readability_TOCHI22.pdf). The material was prose, not code.

The case for our parameters therefore rests on sections (a)–(d), which study prose, letters and digit strings, plus the monospace-specific results in (b).

---

## (f) Measuring confusability of our own glyph pairs in Python

### Viewing model: what blur and size simulate 12–14 px reading

1. **Raster size.** Render at 12, 13, 14 px per em (x-height 6.4–7.6 px), supersampled, then apply a 1 px box filter for the pixel aperture.
2. **Optical and neural blur.** "Visual Gaussian blur has a standard deviation of about B = 0.01549 degrees of visual angle" (0.93′; equivalently a Gaussian scale of 2.33′, or a sech filter of scale 2.16′) [[P] Watson 2012](https://content.wolfram.com/sites/19/2012/02/Watson.pdf). With a pixel of 1.15′–1.82′ (section 0) that is σ = 0.51–0.81 CSS px [M].
3. **Information limit.** A Gaussian of standard deviation σ has half-amplitude frequency 0.1874/σ cycles per px [M, from exp(−2π²σ²f²) = ½]. For an x-height of 7.4 px, the 2 cycles-per-letter cutoff corresponds to σ = 0.69 px and the 1.4 cycles-per-letter cutoff to σ = 0.99 px [M], using the cutoffs of [Legge et al. 1985](https://pubmed.ncbi.nlm.nih.gov/4013091/) and [Kwon & Legge 2012](https://pubmed.ncbi.nlm.nih.gov/22521659/).

The optical estimate and the information-limit estimate agree: **σ = 0.6 px (normal) and σ = 1.0 px (limit) at 14 px/em**. A third level, σ = 1.5 px, stands for dark themes, defocus and parafoveal view [I]. A pupil-dependent optical model exists [[A] Watson 2013](https://pubmed.ncbi.nlm.nih.gov/23729769/) but I could not open the paper to verify its constants.

### Candidate metrics

| # | metric | formula | source | evidence it tracks human confusion |
|---|---|---|---|---|
| 1 | Pixel difference Δ | Δ = Σᵢⱼ \|I₁(i,j) − I₂(i,j)\| on binary N×N bitmaps; MSE = Δ/N²; PSNR = 20 log₁₀N − 10 log₁₀Δ | [[P] Suzuki et al. 2019, ShamFinder](https://arxiv.org/abs/1909.07539) | 32×32 Unifont bitmaps, threshold Δ ≤ 4; mean human confusability rating (1–5) was 3.57 at Δ = 4 and 2.57 at Δ = 5 |
| 2 | Overlap / IoU | IoU = \|A∩B\| / \|A∪B\| = (\|A\|+\|B\|−Δ)/(\|A\|+\|B\|+Δ) [M, identity] | template-overlap models tested by [Gervais et al. 1984](https://pubmed.ncbi.nlm.nih.gov/6238125/) | overlap was beaten by the CSF-filtered model (below) |
| 3 | SSIM | SSIM(x,y) = (2μₓμᵧ+C₁)(2σₓᵧ+C₂) / ((μₓ²+μᵧ²+C₁)(σₓ²+σᵧ²+C₂)), C₁=(0.01L)², C₂=(0.03L)², 11×11 Gaussian window, σ = 1.5 samples | [[P] Wang et al. 2004](https://www.cns.nyu.edu/pub/eero/wang03-reprint.pdf) | designed for image quality; ShamFinder chose Δ over it for glyphs |
| 4 | CSF-filtered spectral distance | distance between Fourier transforms of the letters after weighting by the human contrast sensitivity function | [[A] Gervais et al. 1984](https://pubmed.ncbi.nlm.nih.gov/6238125/) | r = .70 with a 26×26 uppercase confusion matrix (3,900 trials), the best of template, feature and Fourier models |
| 5 | Ideal-observer template model | optical filter → neural filter → noise → optimal classifier; discriminability grows with the energy of the filtered difference image. "Contrast difference energy: the average of the squared distances between the letter images and the average letter image" | [[A] Watson & Ahumada 2008](https://pubmed.ncbi.nlm.nih.gov/18484856/), [2012](https://pubmed.ncbi.nlm.nih.gov/23024356/), [2015](https://pubmed.ncbi.nlm.nih.gov/25761333/); CSF-limited version [Chung et al. 2002](https://pubmed.ncbi.nlm.nih.gov/12207975/), [Kwon & Legge 2011](https://pubmed.ncbi.nlm.nih.gov/21854800/) | off-diagonal confusion correlations 0.5–0.8 across seven optotype sets, better than a geometric-moment model |
| 6 | Perimetric complexity | P²/A (Pelli) or P²/(4πA) (Watson; a disc = 1), P = inside plus outside perimeter, A = ink area; "visual" variant blurs first | [[A] Pelli et al. 2006](https://pubmed.ncbi.nlm.nih.gov/16808957/), [[P] Watson 2012](https://content.wolfram.com/sites/19/2012/02/Watson.pdf) | identification "efficiency is inversely proportional to perimetric complexity"; a per-glyph cost, not a pair metric |
| 7 | Learned embedding | Siamese CNN, d = ‖g(x₁) − g(x₂)‖₂, contrastive loss with margin 1, strings rendered 150×12 px in Arial | [[P] Woodbridge et al. 2018](https://arxiv.org/abs/1805.09738) | 13–45% higher ROC AUC than edit distances on spoof detection; trained on synthetic spoofs, not human confusions |
| 8 | Skeleton equality | skeleton(X) = skeleton(Y) | [[P] UTS #39](https://www.unicode.org/reports/tr39/) | a curated list, not a metric; use it as the set of pairs that must pass |

### The metric I implemented and tested [M]

Metric 5 in its simplest form. For glyph images a, b rendered in their monospace cells:

A = G_σ ∗ box₁ₚₓ ∗ a,  D(a,b) = ‖A − B‖₂ / √((‖A‖₂² + ‖B‖₂²)/2)

D runs from 0 (identical) to √2 (disjoint); for equal energies D = √(2(1−ρ)) with ρ the correlation. Two variants: cell-registered, and minimum over shifts of ±1 px in 0.5 px steps. The whole 62-character matrix for four fonts at two blur levels runs in about 5 s with numpy and Pillow.

**Validation against human data.** I parsed Mueller and Weidemann's two 26×26 accuracy matrices from their Tables 2–3, symmetrised the logit accuracies (which cancels bias), removed additive letter effects by least squares (leaving their δ), and correlated with D over 325 pairs. Courier New Bold is not installed, so FreeMono Bold and Courier 10 Pitch Bold stood in.

| font used for D | σ = 0 | σ = 0.6 px | σ = 1.0 px | σ = 1.5 px | σ = 2.5 px | 1 − IoU |
|---|---|---|---|---|---|---|
| FreeMono Bold | 0.305 | **0.333** | 0.315 | 0.260 | 0.186 | 0.291 |
| Courier 10 Pitch Bold | 0.285 | 0.292 | 0.253 | 0.186 | 0.122 | 0.277 |
| Liberation Mono Bold (wrong design) | 0.277 | 0.278 | 0.253 | 0.181 | 0.108 | 0.278 |
| DejaVu Sans Mono Bold (wrong design) | 0.260 | 0.258 | 0.233 | 0.175 | 0.104 | 0.266 |

(Spearman correlation with the mean similarity residual of the two experiments.)

Reading of this result: the correlation is weak (at most 0.33). The human data set is itself noisy for this purpose: the similarity residuals of the two experiments, which differ only in mask character, correlate at 0.23, and their symmetrised accuracies at −0.004. The metric does best with the Courier-like font and σ = 0.6 px, and degrades with more blur. Plain IoU is nearly as good. **This metric is a screening tool for relative comparisons against reference fonts; it is not a validated predictor of human error rates.** The published models that reach 0.5–0.8 add a contrast sensitivity function and were tested on naming under size or contrast limits, a task closer to ours than masked 2-AFC.

---

## Where sources disagree

1. **Polarity.** Legge et al. 1985 and 1987 found no polarity effect on reading rate; Buchner, Piepenbrock and Dobres found a consistent positive-polarity advantage, growing as size falls. Buchner et al. 2009 reconcile them: the effect vanishes at equal display luminance.
2. **Fixed versus proportional pitch.** Proportional is about 5% faster at comfortable sizes (Mansfield; Arditi), or no different (Rayner; Black & Watts), and fixed pitch is better near the acuity limit (Arditi; Mansfield; Tarita-Nistor). Mansfield reports that Morris et al. found no fixed-pitch advantage, and attributes it to their not testing below CPS.
3. **Extra letter spacing.** Crowding theory predicts a benefit; Chung 2002 and Yu 2007 found none beyond standard spacing in Courier; Xiong 2018 found wider-spaced fonts permit smaller print (better CPS and acuity) at the cost of maximum speed.
4. **Bold.** Readers with low vision prefer bold; Bernard 2013 found no speed benefit from 0.72× to 1.89× and a loss beyond; Sheedy 2005 found a threshold benefit only from the thinnest weight.
5. **Complexity.** Pelli 2006: efficiency falls with perimetric complexity. Xiong 2018: higher complexity gave slightly *better* acuity in normal readers (0.015–0.035 logMAR across a range of 65.88–116.07) and no effect in MD. Beier 2018: crowded digits profit from a short skeleton.
6. **Open apertures.** DIN and DBSV recommend open a, c, e, o, s; Beier & Larson 2010 found no benefit of opening c, and for e only that extreme closure hurts.
7. **The foot of 1.** Beier 2018 recommends no bottom crossbar for crowded digit strings; code needs 1 to differ from l and I, which a foot helps. My measurement shows 1/I at 0.25 in all three screen fonts, their weakest pair of the three.
8. **Identifier style.** Underscore 13.5% faster (Sharif & Maletic) against camel case better or no difference (Binkley).

---

## What this means for our font

Each decision names its basis. "Gate" means a number the build should test on every master.

### Proportions

| parameter | value | basis |
|---|---|---|
| Design size | Treat 12–14 px as caption size: draw for 0.12°–0.19° x-height | section 0 [M]; optical scale, Legge & Bigelow [P] |
| Advance width | 600 / 1000 em, no narrower | centre-to-centre 0.16°–0.25° is already at the foveal critical spacing S₀ of 0.1°–0.2° [P, M] |
| x-height | **540 / 1000 em** (range 530–550) | screen-designed faces average 0.52, SD 0.03 [P]; Verdana at 0.55 most legible [A]; references measure 0.527–0.549 [M] |
| Advance ÷ x-height | 1.11; gate ≥ 1.09 | wider relative spacing gives smaller CPS (Xiong) [P]; references 1.09–1.14 [M]. This is why x-height should not exceed 550 |
| Advance ÷ width of x | 1.14–1.20 | the optimum in Courier is 1.16 (Chung; Yu) [A, P]; references 1.14–1.20 [M] |
| Ascender | 760; cap height 720 | ascenders are the strongest cue (Bouma) [A]; h/b, n/h are among the closest lowercase pairs at D 0.24–0.31 [M]; an ascender above cap height separates l from I [I] |
| Descender | −200 to −210 | same cue; references 0.18–0.21 [M] |

### Stroke

| parameter | value | basis |
|---|---|---|
| Regular vertical stem | **88–90 / 1000 em = 16–17% of x-height** | Courier 0.165 and the centre of the speed plateau (Bernard) [P]; DIN 10–20%, consultation text 13–20% [S]; references 0.163–0.169 [M] |
| Lightest weight meant for reading | stem ≥ 70 (13% of x-height); absolute floor 54 (10%) | DIN consultation and reading minima [S]; speed fell 23.3% at 0.27× (4.5% of x-height) [P] |
| Bold | stem ≤ 165 (1.89× regular, 31% of x-height), and only if counters stay open | plateau ends at 1.89×; loss attributed to closing counters and gaps [P] |
| Horizontal strokes | ≥ 65 (12% of x-height); stem:horizontal 1.10–1.25 | DIN hairline minimum [S]; high stroke contrast impairs recognition in bold (Beier & Oderkerk) [A]; references 1.11–1.33 [M] |
| n counter (between stems) | 240–260 = 0.45–0.48 of x-height | DIN normal width ≈ 0.50 [S]; references 0.43–0.47 [M] |
| n-to-n gap ÷ n counter | 0.72–0.78 (with stem 88 and counter 242, gap 182, side bearings 91) | DIN 2024: 70–75% consultation text, 73–78% signage [S]; references 0.71–0.77 [M] |
| Weight axis | Continuous; regular at the values above | individual differences are large (Wallace: 35%) [P]; no measured optimum exists for dark themes |

### Letterforms that the evidence decides

1. **a**: double-storey in upright and italic. Single-storey a is misread as o and q [P].
2. **l**: top-left serif and a curved right foot filling the cell. The wide tailed l beat serifed and plain forms [P]. **i** and **j**: slab on top, j with a broad hook; fill the cell [P]. The monospace cell makes the "widen narrow letters" recommendation free.
3. **I**: full-width serifs top and bottom. **1**: flag, and a foot shorter than I's serifs or none; decide by gate. **|**: no serifs, taller than ascender and deeper than descender. Gate: every pair among 1, l, I, | at D ≥ 0.40 (σ = 1.0 px, 14 px). References manage 0.41–0.57 except 1/I at 0.25–0.28 [M].
4. **0 versus O, D, 8**: separate by outline first, then by mark. Make 0 at least 15% narrower than O; keep O wide and D flat-backed with square corners; add a slash or dot at least one stem thick. Gate: D(0,O) ≥ 0.30, D(D,O) ≥ 0.25, D(0,8) ≥ 0.25. References score 0.14–0.22, 0.12–0.18 and 0.17–0.18; the unmarked but narrow FreeMono zero scores 0.31 [M]. Zero must be full figure height: short zeros were identified 24% of the time against 89% [P].
5. **8/B and 5/S**: the worst pairs in every screen reference (0.11–0.19) [M] and on Grissinger's list [S]. Give B a flat left stem with visible corners and unequal bowls, 8 a narrower top and a crossing waist; give 5 a flat top bar and a sharp corner, S none. Gate: ≥ 0.25.
6. **e**: crossbar at or above mid-height (position below 0.61 of height gave 92% correct against 10%) [P]; aperture not pinched. **c**: aperture is a free aesthetic choice [P].
7. **g, q, 9**: Bouma's /g q/ group [A]; measured g/q 0.25–0.28 [M]. Give q a straight stem with a spur or flick and g a curved hooked tail; 9 and 3 with open apertures [A]. Gate: g/q ≥ 0.35.
8. **7**: straight leg, no serif on the bar [A]. **t**: asymmetric crossbar and curved foot, not widened into c [P]. **u**: keep its stem; a tailless u did not help [P]. **f**: may descend in italic [P].
9. **Punctuation and brackets** [I, supported by M]: period and comma differ by 0.37–0.50 after a 1 px shift, braces and parentheses by 0.17–0.30. Dot diameter ≥ 1.3 stems; comma descends at least 0.15 em; brace cusp at least 1.5 stems deep; square brackets with arms ≥ 2 stems. Gate: ≥ 0.40 best-shift for ., :; '\` and ≥ 0.35 for ({ [( }].
10. **Underscore**: full advance width so adjacent underscores join, weight equal to the horizontal stroke [I]; the only code-specific finding is that underscore-separated identifiers were read 13.5% faster in one study [S].

### Polarity

- Ship one design for both polarities. Luminance, not polarity, causes the deficit [A], and no study measures an optimal dark-mode weight.
- Document for users: in dark themes raise the size by 10% [S], and prefer a dark grey to a true-black background [I, from Kremkow's grey-background result].
- Because a monospace cannot add DIN's 2% tracking, hold the counter and aperture gates at σ = 1.5 px as well as 1.0 px, so the design tolerates the larger pupil's blur [I].
- Offer weights between 350 and 450 so users can thin strokes slightly on dark grounds; irradiation makes light strokes look heavier [P, I].

### Ligatures and proportional variants

No evidence supports or refutes code ligatures. Make them opt-in features, off by default, and make no legibility claim for them. Proportional and fixed pitch read equally fast at normal sizes [P], and fixed pitch is better near the acuity limit [P, A]; that is the evidence-based argument for monospace in terminals beyond alignment.

### Measurement plan

1. Compute for every master: x-height/em, stem/x-height, stem:horizontal, advance/x-height, advance/x-width, n counter/x-height, gap/counter, perimetric complexity (references: mean P²/A over a–z of 72–76 [M]; a design far above 80 is spending strokes on detail that 7 px cannot show [I]).
2. Compute D for all pairs at 13 and 14 px/em, σ ∈ {0.6, 1.0, 1.5} px, registered and best-shift. Gates: the watched pairs above; no alphanumeric pair below 0.20 at σ = 1.0 px; median not below the references' 0.62–0.66.
3. Report every gate beside the same number for JetBrains Mono, DejaVu Sans Mono and Liberation Mono, so each claim is "better than reference X by Y" rather than an absolute legibility claim.
4. Upgrade the metric before trusting it further: add a contrast sensitivity weighting (metric 4/5) and re-validate against a naming confusion matrix obtained under size limitation. The present validation (ρ ≤ 0.33) does not license absolute claims.
5. State in the documentation that nothing here has been tested on people reading code, because no such study exists.

---

## Sources I could not open

- Full text of Pelli et al. 2006 and 2007, Majaj et al. 2002, Watson 2013, Watson & Ahumada 2008, 2012, 2015 (journal and author sites returned 403). Cited from abstracts; the constants of Watson's pupil-dependent MTF formula are not verified and not used.
- DIN 1450:2024-11 and ISO 9241-303 (paywalled). DIN values are from DBSV's leserlich.info and its calculator code. No ISO 9241-303 value is used.
- Bouma 1971, Geyer 1977, Townsend 1971, Gilmore et al. 1979, Simpson et al. 2013 full matrices (publisher blocks). Bouma and Simpson cited from abstracts; the others only through Mueller & Weidemann's review.
- Beier et al. 2018 (numerals) and Chaparro et al. 2011: abstracts only. Fox et al. 2007 not found; its e and 0 results are taken from Merkle & Chaparro 2009, which reports the same experiment.
- Dobres, Reimer & Chahine 2016 on font weight and rendering; Jarosch et al. 2019 on monospaced versus proportional sentence reading. Not read, not used.

## Appendix: scripts and data from this session

All under `/tmp/claude-0/-home-user-experiments/a86123d7-7ed9-5f3d-9952-1d096afee651/scratchpad/research/`:

- `tools/angles.py`: visual angles, minimum sizes, stroke widths in font units.
- `tools/confusability_proto.py`: font metrics, perimetric complexity (4-direction Cauchy–Crofton perimeter), blurred-template distance for 62 characters and symbol pairs.
- `tools/validate_mw.py` with `tools/parse_mw.py`: validation against Mueller & Weidemann's Tables 2–3 (`dl/mueller2012/tables.json`).
- `tools/xwidth.py`, `tools/zero_check.py`: advance/x-width; zero against O.
- `tools/ascii_conf.py`: ASCII-to-ASCII entries of `dl/confusables/confusables.txt`.
- `dl/`: downloaded sources as text.

Caveats on my measurements: Pillow rasterisation without hinting; Pillow's Gaussian is a box-filter approximation; the perimeter estimator is exact for circles and about 5% low for axis-aligned squares; fonts are the versions installed on this machine.
