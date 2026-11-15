# How the designers of code typefaces explain their decisions

Research for the new monospaced family (code, plain-text mathematics, terminal UIs). Compiled 2026-11-14.

## 0. Scope, method and how to read the evidence

**What was read.** The designers' own material for JetBrains Mono, Input, Iosevka, Recursive, Monaspace, Commit Mono,
Intel One Mono, IBM Plex Mono, Source Code Pro, Cascadia Code, Fira Code/Mono, Go Mono, Lucida Console, Berkeley Mono,
Triplicate, MonoLisa, 0xProto, Atkinson Hyperlegible Mono, Geist Mono, Maple Mono, JuliaMono and Departure Mono.
For Operator Mono the foundry's own post could not be read (it is rendered by script), so its designers are quoted
from a Wired interview, which is a secondary source.

**What was measured.** Designers publish few numbers. To get them, I downloaded the open-licensed font files and measured
the outlines with fontTools (bounding boxes, and scan-lines through flattened outlines for stem and counter widths).
Every measured number below is in **thousandths of the em** (so 600 = 0.600 em) and is for the Regular weight
(variable fonts instantiated at `wght=400`; Recursive at `MONO=1, CASL=0`). The files, versions and URLs are in the
appendix. Commercial faces (Input, Berkeley Mono, Operator Mono, MonoLisa, Triplicate, Lucida Console) were not measured.

**Evidence labels** used in this report:

- **[P]** primary: the designer's or publisher's own text, read directly.
- **[M]** measured by me from the font file named in the appendix.
- **[S]** secondary: journalism quoting the designer.
- **[I]** my inference.

Scripts and raw output are in `/tmp/claude-0/-home-user-experiments/a86123d7-7ed9-5f3d-9952-1d096afee651/scratchpad/research/cfd/`
(`tools/measure.py`, `measure.json`, `measure_tables.txt`, `stats.txt`, `weights.txt`, `sheets/*.png`).

---

## (a) Proportions: x-height, cap height, ascender, descender, advance, line height

### What the designers say

- **An advance of 0.6 em is the stated convention.** Paul D. Hunt condensed the capitals of Source Sans "to fit within
  the standard monowidth of 60% of the em square" [P]
  ([Adobe Typekit blog, 2012](https://blog.typekit.com/2012/09/24/source-code-pro/)). In the comments he adds that
  "Consolas is narrower than most monospaced fonts at 55% of the Em square, where I stuck with 60%", and calls 60%
  the width "used by most monospaced fonts" [P] (same page).
- **Go Mono keeps Courier's width and raises the x-height.** "Go Mono fonts have the same x-height as Go sans-serif fonts,
  53% of the body size. Go Mono looks almost 18% bigger than Courier, which has an x-height 45% of body size. Yet Go Mono
  has the same width as Courier, so the bigger look is gained with no loss of economy in characters per line." It sets
  10 characters per inch at 12 pt and 12 per inch at 10 pt [P] ([Go blog, Bigelow's notes](https://go.dev/blog/go-fonts)).
- **Lucida: x-height about 53% of the body, for two stated reasons.** A big x-height "makes the typeface appear
  perceptually bigger", and "provides more pixels for better definition of features in the x-height region, which
  typically carries more information than ascenders and descenders" [P]
  ([How and Why We Designed Lucida](https://lucidafonts.com/blogs/bigelow-holmes-blog/how-and-why-we-designed-lucida)).
- **Lucida: capitals shorter than ascenders, on purpose.** "we drew ascenders taller than capitals, to distinguish
  lower-case 'l' from capital 'I', and also to de-emphasize capitals slightly so that all-capital composition like
  acronyms, common in high-tech prose ... did not unduly interrupt the pattern of text" [P] (same page; the same reason
  is in [Notes on Lucida designs](https://www.tug.org/store/lucida/designnotes.html)).
- **Lucida: stem weight is given as a ratio.** "The ratio of vertical stem thickness to x-height in Lucida normal weight
  fonts is 1 to 5.5", chosen "slightly dark ... to compensate for erosion around the edges of black letters on white
  background screens". Later weights: Lite 1:7.3, Book 1:6.3, Text 1:5.9, Normal 1:5.5, Thick 1:5.2, Extra Thick 1:4.9 [P]
  (same page). Lucida Sans keeps a thick-to-thin contrast of "roughly 4 to 3" [P] (same page).
- **JetBrains Mono maximises the lowercase at standard width.** "Characters remain standard in width, but the height of
  the lowercase is maximized. This approach keeps code lines to the length that developers expect, and it helps improve
  rendering since each letter occupies more pixels." It contrasts Consolas, whose letters are "slightly wider" but
  "rather small, which forces you to increase the size by one point" [P] ([jetbrains.com/lp/mono](https://www.jetbrains.com/lp/mono/)).
  Recommended settings on the same page: "Size: 13, Line spacing: 1.2" [P].
- **Source Code Pro argues the opposite about x-height.** Hunt's first complaint about existing faces: "many monospaced
  fonts force lowercase letters with a very large x-height into a single width, resulting in overly condensed letter
  forms which result in words and text with a monotonous rhythm". He kept "the moderate x-height of the parent family",
  noting that "the greater difference in letter heights between upper and lowercase makes it much simpler to
  differentiate lowercase o from uppercase O" [P] ([Source Code Pro post](https://blog.typekit.com/2012/09/24/source-code-pro/)).
- **Source Code Pro makes figures shorter than capitals.** "The figures of Source Sans were made somewhat smaller than the
  capital height ... I kept this feature in Source Code, where this difference also serves to further distinguish 0
  from O, and 1 from l" [P] (same page). Measured: figure height 638, cap height 656 [M].
- **Iosevka publishes its vertical metrics as build parameters.** `cap = 735`, `ascender = 735`, `xHeight = 520`,
  `leading = 1250` ("Default line height times 1000"), `symbolMid = 340` ("Center of parens, maths, geometrics"),
  `parenSize = 966`, per 1000-unit em [P]
  ([params/parameters.toml](https://raw.githubusercontent.com/be5invis/Iosevka/main/params/parameters.toml)). The default
  width is 500 units, with wider grades at 547, 600, 657 and 720 [P]
  ([params/shape-width.toml](https://raw.githubusercontent.com/be5invis/Iosevka/main/params/shape-width.toml)); the font
  describes itself as "Spatial efficient" [P] (parameters.toml).
- **MonoLisa widens the cell.** "MonoLisa is ~7% wider compared to other monospaced fonts"; "increased character width
  helped us design a typeface with more natural, open forms" [P] ([monolisa.dev](https://www.monolisa.dev/)).
- **Maple Mono ships three widths**: "Default (600), narrow (550), and slim (500) Latin glyph widths", and CJK glyphs at
  exactly twice the Latin width [P] ([README](https://raw.githubusercontent.com/subframe7536/maple-font/variable/README.md)).
- **Input makes line height a user choice.** "Many source code editors don't offer their users control over line spacing,
  instead choosing to rely on the metrics built into the font", so the download form rebuilds the font's metrics [P]
  ([input.djr.com/info](https://input.djr.com/info/)). The form's slider runs from 0.9× to 1.8× in steps of 0.1,
  default 1.2× [P] ([input.djr.com/download](https://input.djr.com/download/)).
- **Input and Departure Mono start from a pixel grid.** Input "was drawn over an 11-pixel grid", following "Matthew
  Carter's process for creating Verdana" [P] ([input.djr.com/info](https://input.djr.com/info/)). Departure Mono asks
  users to "set the font size to increments of 11px" [P]
  ([README](https://raw.githubusercontent.com/rektdeckard/departure-mono/main/README.md)). Measured, Departure Mono is an
  11-pixel em with a 7-pixel advance, 6-pixel x-height, 8-pixel capitals, 2-pixel descender and a 14-pixel line [M].
- **Recursive shares vertical metrics across its Mono and Sans**: "vertical metrics such as line height, cap height, and
  x-height are shared across the entire Monospace axis" [P] ([recursive.design](https://www.recursive.design/)).
- **Intel One Mono gives a size floor**: "7 points and larger in print, 9 pixels and larger on screen" [P]
  ([README](https://raw.githubusercontent.com/intel/intel-one-mono/main/README.md)).
- **Berkeley Mono** claims "a comfortable line-height" without a number [P] ([usgraphics.com](https://usgraphics.com/products/berkeley-mono)).

### What the files say [M]

| Font (version measured) | advance | x-height | cap | ascender (h) | descender (p) | figure (7) | x/cap | x/advance | line height (hhea) | hhea asc/desc/gap |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| JetBrains Mono 2.305 | 600 | 550 | 730 | 730 | -180 | 730 | 0.753 | 0.917 | 1.320 | 1020/-300/0 |
| Source Code Pro 2.042 | 600 | 486 | 656 | 712 | -205 | 638 | 0.741 | 0.810 | 1.257 | 984/-273/0 |
| Iosevka 22.1.2 | 500 | 520 | 735 | 735 | -215 | 735 | 0.707 | 1.040 | 1.250 | 965/-215/70 |
| Recursive Mono Linear 1.085 | 600 | 532 | 700 | 750 | -200 | 700 | 0.760 | 0.886 | 1.200 | 950/-250/0 |
| Monaspace Neon 1.400 | 620 | 514 | 730 | 765 | -194 | 730 | 0.703 | 0.828 | 1.245 | 945/-200/100 |
| Commit Mono 1.143 | 600 | 540 | 700 | 740 | -200 | 700 | 0.771 | 0.900 | 1.100 | 900/-200/0 |
| Intel One Mono 1.005 | 614 | 465 | 655 | 710 | -230 | 655 | 0.710 | 0.757 | 1.380 | 1090/-290/0 |
| IBM Plex Mono 2.3 | 600 | 516 | 698 | 740 | -200 | 698 | 0.739 | 0.860 | 1.300 | 1025/-275/0 |
| Cascadia Code 2407.024 | 586 | 518 | 693 | 732 | -225 | 693 | 0.746 | 0.883 | 1.162 | 928/-234/0 |
| Fira Mono 3.206 | 600 | 527 | 689 | 747 | -212 | 689 | 0.765 | 0.878 | 1.200 | 935/-265/0 |
| Go Mono 2.010 | 600 | 530 | 723 | 771 | -193 | 723 | 0.734 | 0.884 | 1.156 | 945/-211/0 |
| 0xProto 2.502 | 620 | 550 | 710 | 750 | -197 | 710 | 0.775 | 0.887 | 1.560 | 1130/-430/0 |
| Atkinson Hyperlegible Mono 2.001 | 632 | 496 | 668 | 708 | -162 | 668 | 0.743 | 0.785 | 1.300 | 984/-316/0 |
| Geist Mono 1.701 | 600 | 530 | 710 | 710 | -150 | 710 | 0.746 | 0.883 | 1.300 | 1005/-295/0 |
| Maple Mono 7.800 | 600 | 560 | 740 | 740 | -190 | 730 | 0.757 | 0.933 | 1.320 | 1020/-300/0 |
| JuliaMono 0.63.2 | 600 | 550 | 725 | 790 | -190 | 725 | 0.759 | 0.917 | 1.175 | 950/-225/0 |
| Departure Mono 1.500 | 636 | 545 | 727 | 727 | -182 | 727 | 0.750 | 0.857 | 1.273 | 1000/-273/0 |
| (ref) Hack 3.003 | 602 | 547 | 729 | 760 | -208 | 729 | 0.750 | 0.908 | 1.164 | 928/-236/0 |
| (ref) Roboto Mono 3.001 | 600 | 528 | 711 | 750 | -203 | 711 | 0.743 | 0.880 | 1.319 | 1048/-271/0 |
| (ref) Inconsolata 3.001 | 500 | 457 | 623 | 665 | -167 | 623 | 0.734 | 0.914 | 1.049 | 859/-190/0 |
| (ref) Courier Prime 3.018 | 600 | 451 | 580 | 641 | -189 | 580 | 0.778 | 0.752 | 1.123 | 781/-342/0 |

Across the 16 current designer faces (the first 16 rows; Departure Mono and the reference rows excluded):

| Quantity | min | lower quartile | median | upper quartile | max |
|---|---:|---:|---:|---:|---:|
| Advance | 500 | 600 | 600 | 611 | 632 |
| x-height | 465 | 514 | 528 | 548 | 560 |
| Cap height | 655 | 690 | 705 | 729 | 740 |
| Ascender (top of `h`) | 708 | 716 | 740 | 750 | 790 |
| Descender (bottom of `p`) | −230 | −210 | −198 | −190 | −150 |
| Ascender − cap height | 0 | 9 | 40 | 54 | 65 |
| x-height / cap height | 0.703 | 0.735 | 0.746 | 0.760 | 0.775 |
| x-height / advance | 0.757 | 0.836 | 0.883 | 0.913 | 1.040 |
| Default line height (hhea, em) | 1.100 | 1.181 | 1.253 | 1.315 | 1.560 |

Observations:

- Ten of the 16 have an advance of exactly 600. The wider ones are the newer or accessibility-led designs: Intel One
  Mono 614, Monaspace 620, 0xProto 620, Atkinson Hyperlegible Mono 632. The narrow ones are Cascadia Code 586 and
  Iosevka 500 [M].
- The published claims check out: Go Mono's x-height measures 530 (stated 53.0%), Source Code Pro's advance 600 (stated
  60%), Iosevka's 520/735/1.25 match its parameters, and Courier Prime (a Courier redrawing) measures 451 against
  Bigelow's 45% for Courier [M].
- The two faces made for low-vision readers have the *lowest* x-height-to-advance ratios of the set: Intel One Mono
  0.757 (x-height 465, advance 614) and Atkinson Hyperlegible Mono 0.785 (496, 632). They buy letter width, not letter
  height [M]. Reading that as intent is my inference [I].
- Four of the 16 make ascenders equal to capitals (JetBrains Mono, Iosevka, Geist Mono, Maple Mono), as does Departure
  Mono. The other twelve follow Lucida's rule, with ascenders 35–65 units above the capitals [M].
- Two faces make figures shorter than capitals: Source Code Pro (638 against 656) and Maple Mono (730 against 740).
  The other 14 draw figures at cap height [M].
- Default line height is not a consensus: 1.10 (Commit Mono) to 1.56 (0xProto), median 1.25. The explicit statements
  cluster at 1.2 to 1.25: JetBrains recommends 1.2, Input defaults to 1.2, Iosevka builds 1.25 [P][M].

### Italic angle and weight range

- Declared italic angles (`post.italicAngle`): 9° for JetBrains Mono, IBM Plex Mono, Iosevka, JuliaMono and 0xProto;
  9.5° Commit Mono; 10° Cascadia Code and Maple Mono; 11° Source Code Pro, Go Mono and Monaspace Neon; 12° Atkinson
  Hyperlegible Mono; 16° Intel One Mono. Median 10° [M]. JetBrains gives a reason: "Typically, the angle is about
  11°–12°. JetBrains Mono uses a 9° angle; this maintains the optimal contrast to minimize distraction and eye strain"
  [P] ([jetbrains.com/lp/mono](https://www.jetbrains.com/lp/mono/)). Recursive's slant axis runs 0 to −15, with the advice
  that "in text, it can be useful to use a partial slant of around -9" [P]
  ([README](https://raw.githubusercontent.com/arrowtype/recursive/main/README.md)).
- Go Mono's italics "are oblique versions of the romans, with the exception that the italic lowercase 'a' is redesigned
  as a cursive single-story form" [P] ([Go blog](https://go.dev/blog/go-fonts)). JetBrains Mono takes "a", "y" and "f"
  from the true italic [P] (same JetBrains page).
- Bold stems are about 1.5 times the Regular stem. Go states it: "The bold stem thickness is 1.5 times thicker than the
  normal weight", and notes that "Because the letter width of monospaced bold is identical to the width of monospaced
  normal, the bold Mono appears slightly bolder than the proportional Go Bold" [P] ([Go blog](https://go.dev/blog/go-fonts)).
  Measured Bold/Regular stem ratios: Cascadia Code 1.28, JetBrains Mono 1.39, Iosevka 1.42, Commit Mono 1.43, Go Mono 1.44,
  0xProto 1.44, Recursive 1.48, Monaspace Neon 1.52, Geist Mono 1.61, Atkinson 1.65, Intel One Mono 1.69, Source Code
  Pro 1.79, IBM Plex Mono 1.85 [M]. At weight 700 the stem is 0.20–0.25 of the advance in every family measured [M].
- The period does not scale with the stem. In JetBrains Mono the period is 2.92 stems wide at Thin, 1.82 at Regular
  and 1.49 at Bold; in Source Code Pro 3.47, 1.98 and 1.58 [M]. Iosevka encodes this directly: `periodSize` is 55 at
  weight 100, 140 at weight 400 and 200 at weight 900, against strokes of 18, 70 and 114 [P]
  ([params/shape-weight.toml](https://raw.githubusercontent.com/be5invis/Iosevka/main/params/shape-weight.toml)).

---

## (b) The monospace problem: narrow letters, wide letters, texture

### What the designers say

- **The problem, stated by the people who draw it.**
  - David Jonathan Ross: "wide characters are forced to squeeze; narrow characters are forced to stretch. Uppercase
    letters look skinny next to lowercase, and bold characters don't have enough room to get very bold" [P]
    ([input.djr.com/info](https://input.djr.com/info/)).
  - Monaspace: "Narrow letters like l and i must be designed with exaggerated serifs to better fill the monospace box.
    Even with these synthetic additions, these narrow letters have more space than they need. Wide letters like m and w
    are crammed into their boxes ... Their strokes are thinner, and the negative space inside the glyph is also
    compromised" [P] ([monaspace.githubnext.com](https://monaspace.githubnext.com/)).
  - JuliaMono: "It's like fitting every human being of whatever shape or size into identical airplane seats ... There's
    never quite enough room for a nice-looking 'm' or 'w'" [P] ([juliamono.netlify.app](https://juliamono.netlify.app/)).
- **Hunt's three failure modes** are the most useful checklist: an x-height so large that letters are "overly condensed"
  with "a monotonous rhythm"; lowercase "that leave too much space in between letters, causing words and strings to not
  hold together"; and details "too fussy" for code. His aim for the lowercase: "extend them enough so that words and
  strings hold together, while preventing them from becoming so wide that they appear too much of a caricature" [P]
  ([Source Code Pro post](https://blog.typekit.com/2012/09/24/source-code-pro/)).
- **Serifs are added only where there would be a hole.** Hunt: "only adding serifs to the tops of i, j, and l in areas
  that would seem like empty gaps otherwise"; and for the capitals, "Only the M and the W needed to be more heavily
  modified. I also swapped out the simple, single-stroke uppercase I with a serifed version to better fill out the
  advance width" [P] (same page).
- **Go Mono goes all the way to slabs.** "The Go Mono fonts have slab-shaped serifs, giving them a sturdy appearance" [P]
  ([Go blog](https://go.dev/blog/go-fonts)). Bigelow's general observation: "in most digital monospaced sans-serif fonts
  strict modernist design purity is subordinated to legibility ... letters subject to confusion, like capital I and
  lowercase ell, are given serifs" [P] ([Oh, oh, zero!, TUGboat 34:2](https://tug.org/TUGboat/tb34-2/tb107bigelow-zero.pdf)).
- **Operator Mono treats the fill problem as the style.** Andy Clymer "says many of these stylistic choices were an
  effort to get the letters to fill enough space"; "The more you close in those counter spaces, the more blobby they
  look" [S] ([Wired, 2016](https://www.wired.com/2016/02/hoefler-co-s-new-typewriter-inspired-font-is-crafted-for-coders),
  read through a text mirror). Hoefler on weight: "The difference between Courier regular and Courier bold is pretty
  slight in comparison to any other contemporary, unrestricted typeface" [S] (same article).
- **JetBrains Mono squares the rounds.** "The shape of ovals approaches that of rectangular symbols. This makes the whole
  pattern of the text more clear-cut"; with simple forms, "Rendered in small sizes, the text looks crisper" [P]
  ([jetbrains.com/lp/mono](https://www.jetbrains.com/lp/mono/)).
- **MonoLisa and 0xProto name the same texture problem.** MonoLisa: "Monospaced fonts tend to have unevenly distributed
  dark and light space ... MonoLisa carefully compensates for the issue by using unique letter shapes" [P]
  ([monolisa.dev](https://www.monolisa.dev/)). 0xProto: "we've adjusted the font to ensure that the interior of each
  character is sufficiently wide to be easily visible, even at smaller font sizes" [P]
  ([README](https://raw.githubusercontent.com/0xType/0xProto/main/README.md)).
- **Lucida spaces generously and explains why.** The reasons given are optical scale, "tuning the base spatial frequency,
  the alternation of black strokes and white spaces, to the peak sensitivity of the human visual system", and
  compensation for crowding. The target was three to six cycles per degree; achieved at 16 inches, about 7 cycles per
  degree at 10 pt, 6 at 12 pt, 5 at 14 pt [P]
  ([How and Why We Designed Lucida](https://lucidafonts.com/blogs/bigelow-holmes-blog/how-and-why-we-designed-lucida)).
  The authors add their own caveat: "the jury is still out on whether the hypothetical advantage of generous spacing
  actually improves reading speed and comprehension" [P] (same page).
- **Lucida deepens the arch join to keep `n` from `o`.** "we lowered the arch join, cutting more deeply into the shape
  than in normal grotesque sans-serifs" [P] (same page).
- **Input's escape is proportional fonts designed like monospaced ones**: Input Sans and Serif "adopt the helpful
  attributes of a monospaced design — generous spacing, large punctuation, easily distinguishable characters", and "no
  character is extremely narrow, so a missing character will still make a visible dent in the length of a line" [P]
  ([input.djr.com/info](https://input.djr.com/info/)).
- **Iosevka's escape is a duospaced grid.** Its quasi-proportional builds scale advances in sixths of the base width:
  extra-wide 9/6, M-like 8/6, T-like 7/6, f-like 5/6, i-like 4/6, extra-narrow 3/6 [P]
  ([parameters.toml](https://raw.githubusercontent.com/be5invis/Iosevka/main/params/parameters.toml)).

### How much of the cell is filled [M]

Ink width divided by advance, Regular weight:

| Font | `i` | `l` | `j` | `f` | `t` | `r` | `1` | `I` | `n` | `H` | `m` | `w` | `M` | `W` | `@` |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| JetBrains Mono 2.305 | 0.78 | 0.87 | 0.61 | 0.79 | 0.79 | 0.70 | 0.75 | 0.65 | 0.70 | 0.69 | 0.80 | 0.90 | 0.76 | 0.93 | 0.86 |
| Source Code Pro 2.042 | 0.54 | 0.77 | 0.60 | 0.79 | 0.80 | 0.65 | 0.72 | 0.68 | 0.72 | 0.74 | 0.83 | 0.97 | 0.76 | 0.97 | 0.83 |
| Iosevka 22.1.2 | 0.70 | 0.70 | 0.69 | 0.78 | 0.79 | 0.65 | 0.52 | 0.70 | 0.74 | 0.74 | 0.81 | 0.87 | 0.81 | 0.87 | 0.74 |
| Recursive Mono Linear 1.085 | 0.47 | 0.78 | 0.68 | 0.79 | 0.71 | 0.71 | 0.76 | 0.73 | 0.70 | 0.76 | 0.84 | 0.89 | 0.79 | 0.92 | 0.78 |
| Monaspace Neon 1.400 | 0.74 | 0.74 | 0.58 | 0.82 | 0.79 | 0.78 | 0.76 | 0.73 | 0.69 | 0.72 | 0.76 | 0.96 | 0.77 | 0.95 | 0.89 |
| Commit Mono 1.143 | 0.68 | 0.74 | 0.51 | 0.72 | 0.72 | 0.65 | 0.74 | 0.67 | 0.67 | 0.78 | 0.87 | 0.95 | 0.86 | 1.01 | 0.90 |
| Intel One Mono 1.005 | 0.68 | 0.76 | 0.55 | 0.78 | 0.78 | 0.83 | 0.68 | 0.57 | 0.69 | 0.70 | 0.83 | 0.86 | 0.80 | 0.85 | 0.81 |
| IBM Plex Mono 2.3 | 0.73 | 0.73 | 0.60 | 0.79 | 0.81 | 0.80 | 0.83 | 0.72 | 0.68 | 0.73 | 0.82 | 0.90 | 0.77 | 0.88 | 0.77 |
| Cascadia Code 2407.024 | 0.79 | 0.81 | 0.61 | 0.88 | 0.83 | 0.89 | 0.73 | 0.72 | 0.72 | 0.77 | 0.81 | 0.88 | 0.79 | 0.97 | 0.80 |
| Fira Mono 3.206 | 0.66 | 0.74 | 0.58 | 0.77 | 0.73 | 0.71 | 0.70 | 0.66 | 0.67 | 0.72 | 0.83 | 0.94 | 0.90 | 0.98 | 0.96 |
| Go Mono 2.010 | 0.78 | 0.83 | 0.61 | 0.83 | 0.74 | 0.84 | 0.88 | 0.74 | 0.89 | 0.90 | 0.95 | 0.96 | 0.96 | 0.96 | 0.89 |
| 0xProto 2.502 | 0.72 | 0.67 | 0.62 | 0.88 | 0.74 | 0.82 | 0.74 | 0.71 | 0.72 | 0.74 | 0.86 | 0.87 | 0.89 | 0.90 | 0.88 |
| Atkinson Hyperlegible Mono 2.001 | 0.69 | 0.69 | 0.50 | 0.73 | 0.64 | 0.62 | 0.65 | 0.58 | 0.68 | 0.81 | 0.80 | 0.91 | 0.85 | 0.96 | 0.96 |
| Geist Mono 1.701 | 0.80 | 0.80 | 0.55 | 0.77 | 0.78 | 0.75 | 0.80 | 0.73 | 0.72 | 0.80 | 0.87 | 0.93 | 0.83 | 0.90 | 0.93 |
| Maple Mono 7.800 | 0.78 | 0.80 | 0.67 | 0.82 | 0.81 | 0.70 | 0.78 | 0.65 | 0.68 | 0.69 | 0.82 | 0.88 | 0.80 | 0.88 | 0.93 |
| JuliaMono 0.63.2 | 0.69 | 0.84 | 0.61 | 0.74 | 0.70 | 0.78 | 0.73 | 0.62 | 0.75 | 0.68 | 0.85 | 0.87 | 0.80 | 0.82 | 0.88 |
| Departure Mono 1.500 | 0.71 | 0.71 | 0.57 | 0.71 | 0.71 | 0.71 | 0.71 | 0.71 | 0.71 | 0.71 | 0.71 | 0.71 | 0.71 | 0.71 | 0.71 |
| (ref) Hack 3.003 | 0.67 | 0.71 | 0.48 | 0.70 | 0.73 | 0.64 | 0.70 | 0.67 | 0.69 | 0.78 | 0.83 | 1.00 | 0.86 | 1.00 | 0.93 |
| (ref) Roboto Mono 3.001 | 0.74 | 0.74 | 0.53 | 0.80 | 0.75 | 0.60 | 0.46 | 0.72 | 0.72 | 0.77 | 0.85 | 0.93 | 0.78 | 0.90 | 0.89 |
| (ref) Inconsolata 3.001 | 0.59 | 0.68 | 0.66 | 0.82 | 0.75 | 0.68 | 0.42 | 0.64 | 0.72 | 0.80 | 0.86 | 0.93 | 0.84 | 0.94 | 0.87 |
| (ref) Courier Prime 3.018 | 0.74 | 0.74 | 0.58 | 0.76 | 0.80 | 0.78 | 0.67 | 0.67 | 0.89 | 0.87 | 1.02 | 1.02 | 0.95 | 1.02 | 0.91 |

Medians over the 16 designer faces: `i` 0.71, `l` 0.77, `j` 0.61, `f` 0.79, `t` 0.78, `r` 0.73, `1` 0.74, `I` 0.69,
`n` 0.70, `H` 0.74, `m` 0.83, `w` 0.90, `M` 0.80, `W` 0.93, `@` 0.88 [M].

- With their serifs and tails, `i`, `l`, `1`, `f`, `t` are made as wide as `n` (0.70) or wider. A bare stem would fill
  about 0.15. Source Code Pro (`i` 0.54) and Recursive (`i` 0.47) are the outliers that leave `i` narrow [M].
- `m` is held to about 0.83 of the cell; `w` and `W` are allowed to nearly touch the cell edges (0.90 and 0.93) [M].

### Stems, counters and side bearings [M]

| Font | v-stem (n) | h-stem (H bar) | h/v | x-height/stem | stem/advance | n counter | n LSB+RSB | (LSB+RSB)/counter | m stems | m min stem / n stem | m counter |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| JetBrains Mono 2.305 | 90.0 | 82.0 | 0.91 | 6.11 | 0.150 | 238.0 | 182 | 0.76 | 84/74/84 | 0.82 | 119.0 |
| Source Code Pro 2.042 | 82.0 | 72.0 | 0.88 | 5.93 | 0.137 | 266.0 | 170 | 0.64 | 82/76/82 | 0.93 | 130.0 |
| Iosevka 22.1.2 | 78.0 | 70.0 | 0.90 | 6.67 | 0.156 | 216.0 | 128 | 0.59 | 78/78/78 | 1.00 | 85.0 |
| Recursive Mono Linear 1.085 | 91.5 | 83.5 | 0.91 | 5.81 | 0.152 | 237.3 | 179 | 0.75 | 84/77/84 | 0.84 | 130.1 |
| Monaspace Neon 1.400 | 94.5 | 82.0 | 0.87 | 5.43 | 0.152 | 242.0 | 188 | 0.78 | 86/86/86 | 0.91 | 105.5 |
| Commit Mono 1.143 | 84.0 | 80.0 | 0.95 | 6.43 | 0.140 | 231.0 | 201 | 0.87 | 82/82/82 | 0.98 | 138.0 |
| Intel One Mono 1.005 | 86.0 | 73.0 | 0.85 | 5.41 | 0.140 | 255.0 | 187 | 0.73 | 78/76/79 | 0.88 | 139.0 |
| IBM Plex Mono 2.3 | 80.0 | 73.0 | 0.91 | 6.45 | 0.133 | 250.0 | 190 | 0.76 | 74/74/74 | 0.93 | 135.0 |
| Cascadia Code 2407.024 | 103.5 | 92.8 | 0.90 | 5.00 | 0.177 | 214.8 | 164 | 0.76 | 104/88/104 | 0.85 | 90.8 |
| Fira Mono 3.206 | 84.0 | 71.0 | 0.85 | 6.27 | 0.140 | 233.0 | 199 | 0.85 | 77/78/77 | 0.92 | 133.0 |
| Go Mono 2.010 | 96.7 | 60.5 | 0.63 | 5.48 | 0.161 | 222.7 | 67 | 0.30 | 87/87/87 | 0.90 | 120.6 |
| 0xProto 2.502 | 96.0 | 88.0 | 0.92 | 5.73 | 0.155 | 249.0 | 176 | 0.71 | 95/78/95 | 0.81 | 128.8 |
| Atkinson Hyperlegible Mono 2.001 | 85.3 | 76.7 | 0.90 | 5.81 | 0.135 | 258.3 | 203 | 0.79 | 76/76/76 | 0.89 | 139.6 |
| Geist Mono 1.701 | 84.0 | 84.0 | 1.00 | 6.31 | 0.140 | 264.0 | 168 | 0.64 | 84/84/84 | 1.00 | 134.0 |
| Maple Mono 7.800 | 90.0 | 90.0 | 1.00 | 6.22 | 0.150 | 230.0 | 190 | 0.83 | 94/84/94 | 0.93 | 109.0 |
| JuliaMono 0.63.2 | 87.5 | 79.0 | 0.90 | 6.29 | 0.146 | 266.0 | 150 | 0.56 | 90/90/90 | 1.03 | 114.0 |
| Departure Mono 1.500 | 90.9 | 90.9 | 1.00 | 6.00 | 0.143 | 272.7 | 182 | 0.67 | 91/91/91 | 1.00 | 90.9 |
| (ref) Hack 3.003 | 89.8 | 83.0 | 0.92 | 6.09 | 0.149 | 237.8 | 184 | 0.77 | 82/82/82 | 0.91 | 127.4 |
| (ref) Roboto Mono 3.001 | 90.3 | 76.7 | 0.85 | 5.85 | 0.150 | 254.4 | 165 | 0.65 | 86/86/86 | 0.95 | 126.0 |
| (ref) Inconsolata 3.001 | 70.0 | 60.0 | 0.86 | 6.53 | 0.140 | 219.0 | 141 | 0.64 | 66/67/66 | 0.94 | 116.0 |
| (ref) Courier Prime 3.018 | 73.2 | 66.4 | 0.91 | 6.17 | 0.122 | 235.4 | 67 | 0.28 | 73/73/73 | 1.00 | 131.3 |

Medians over the 16 designer faces [M]:

- Vertical stem 87 units (range 78–104). The horizontal stroke is 0.90 of the vertical. The x-height is 6.0 stems
  (range 5.0–6.7), so the typical code face is slightly lighter than Lucida's 1:5.5.
- The stem is 0.148 of the advance (range 0.133–0.177).
- The counter of `n` is 240 units, or 2.8 stems. The two side bearings of `n` sum to 180 units, 0.76 of its counter.
  So the gap between two `n`s is three-quarters of the gap inside one. (Go Mono's 0.30 is an artefact of its slab
  serifs, which extend the bounding box.)
- Twelve of the 16 thin the stems of `m` by 6% or more. The thinnest stem of `m` is 0.91 of the `n` stem at the median,
  and 0.81–0.84 in 0xProto, JetBrains Mono and Recursive, which thin the middle stem most (JetBrains 84/74/84 against
  90). Commit Mono (0.98), Geist Mono, Iosevka and JuliaMono do not thin `m`.
- The counters of `m` are half the counter of `n` (median ratio 0.51). That is the "cramming" Monaspace describes.

### Texture healing and smart kerning, in units

- **Monaspace texture healing** swaps glyphs for alternates that redistribute white space, inside `calt`. "Narrow
  characters are swapped for ones that cede some of their whitespace, and wider characters are swapped for ones that
  extend to the very edge of their box", and "The resulting text still obeys the monospaced grid" [P]
  ([monaspace.githubnext.com](https://monaspace.githubnext.com/)). The alternates "shift to the left and right, without
  changing the glyph bounds"; givers (`i`) get `.left` and `.right`, takers (`m`) get `.left`, `.right` and `.both` [P]
  ([Texture Healing.md](https://raw.githubusercontent.com/githubnext/monaspace/main/docs/Texture%20Healing.md)).
- Measured in Monaspace Neon 1.400 (advance 620) [M]:

  | Glyph | default ink width | `.left` / `.right` | `.both` | note |
  |---|---:|---:|---:|---|
  | `i` | 460 | 370 | 340 | gives up 90 units (20%) on one side |
  | `l` | 460 | 370 | 340 | |
  | `t` | 492 | 404 | 374 | |
  | `f` | 511 | 407 / 392 | – | |
  | `m` | 469 | 567 | 624 | `.both` spans x = −2..622: wider than the 620 cell |
  | `w` | 594 | 673 | 708 | `.both` overhangs the cell by 44 units each side |
  | `M` | 478 | 536 | 571 | |
  | `W` | 588 | 664 | 689 | |

  A healed `m` is 21% wider than the default, and 33% wider when both neighbours give. The font holds 943 glyphs whose
  names contain left, right or both [M].
- **0xProto adopts the same technique**: it "slightly widens characters like m to improve legibility when they're next
  to narrower characters like i and l, or symbols like periods, colons, and spaces" [P]
  ([README](https://raw.githubusercontent.com/0xType/0xProto/main/README.md)).
- **Commit Mono "smart kerning" moves glyphs and leaves their shapes alone.** "Smart kerning works by looking at single
  letter between two other letters. If the other letters are in different width classes, the middle letter will slide
  closer to the narrow letter"; the example given is "the 'o' is moved 44 units to the right" [P]
  ([commitmono.com](https://commitmono.com/)). The feature code sorts letters into four classes (narrow, normal, larger,
  widest) and substitutes pre-shifted copies named `leftS/M/L` and `rightS/M/L` [P]
  ([ss05_smartkerning.fea](https://raw.githubusercontent.com/eigilnikolajsen/commit-mono/main/src/features/ss05_smartkerning.fea)).
  Measured shifts in version 1.143: about 12, 27–30 and 42–44 units, so at most 7% of the 600-unit advance; ink widths
  are unchanged [M]. The site's claim that this is "improving reading speed and accuracy" comes with no data [P].
- **Commit Mono also moves punctuation next to capitals** ("case sensitive punctuation", `ss03`) [P]
  ([ss03_case.fea](https://raw.githubusercontent.com/eigilnikolajsen/commit-mono/main/src/features/ss03_case.fea)).

---

## (c) The disambiguation set

### The stated principle

- **Differentiate as a system; the exact device matters less.** Bigelow, after surveying fifty years of proposals: "It
  appears that the particular details of individual character designs are not as important as the overall structure of
  the set of differentiations. Zero may be distinguished from capital Oh and from lowercase oh by slashes, dots,
  heights, or shapes" [P] ([Oh, oh, zero!](https://tug.org/TUGboat/tb34-2/tb107bigelow-zero.pdf)).
- **The numeral gets the mark, not the letter.** "the zero is almost always the character that receives an added element,
  usually an internal diagonal slash or an internal dot. The Oh does not get decorated" [P] (same paper).
- **DIN 1450 names four pairs.** Go fonts conform "by differentiating zero from capital O; numeral 1 from capital I (eye)
  and lowercase l (ell); numeral 5 from capital S; and numeral 8 from capital B. The shapes of bowls of b d p q follow
  the natural asymmetries of legible Renaissance handwriting, aiding differentiation" [P] ([Go blog](https://go.dev/blog/go-fonts)).
- **Butterick draws the line between disambiguation and ligatures.** "It's totally fine to redesign individual characters
  to distinguish them from others ... we don't want the lowercase l to look like the digit 1, nor the zero to look like
  a cap O" [P] ([Ligatures in programming fonts: hell no](https://practicaltypography.com/ligatures-in-programming-fonts-hell-no.html)).
  Triplicate's "Code" variant redraws the set he shows as `$te_fl{1234*567~890}` with a leading backtick [P]
  ([Triplicate](https://practicaltypography.com/triplicate.html)).
- **Preferences differ, so ship alternates.** Input: "When it comes to the most readable forms of easily confusable
  characters, everyone has their own preferences", with seven switchable characters: "lowercase i and l (various serif
  arrangements), lowercase a and g (one or two stories), the numeral 0 (dotted or slashed), the asterisk (superscripted,
  or at centered height), and curly braces (curly or straightened)" [P] ([input.djr.com/info](https://input.djr.com/info/)).

### Pair by pair

Forms were read from renderings of each font's default glyphs at 104 px (`sheets/zoom_*.png`) and checked against the
outlines (contour structure of the zero; scan-lines through the feet of `r`, `l`, `i`, `1`) [M]. Eighteen faces were
examined: the 17 in table A plus Hack.

**`0 O o`**

- Default zero forms [M]:
  - forward slash: Iosevka, Recursive, Commit Mono, Intel One Mono, Go Mono, 0xProto, Geist Mono, Maple Mono, Departure Mono (9);
  - reverse slash: Atkinson Hyperlegible Mono (1);
  - dot: JetBrains Mono, Source Code Pro, Monaspace Neon, IBM Plex Mono, Cascadia Code, Fira Mono, JuliaMono (7; JuliaMono's is a diamond);
  - tall oblong dot: Hack (1).
- The other form is usually one feature away: Monaspace `cv01` has plain, slash, reverse slash and cut-out slash [P]
  ([README](https://raw.githubusercontent.com/githubnext/monaspace/main/README.md)); Recursive `ss10` is a dotted zero [P]
  ([recursive-code-config](https://raw.githubusercontent.com/arrowtype/recursive-code-config/main/config.yaml));
  JuliaMono's `zero` feature is a slashed zero [P] ([juliamono.netlify.app](https://juliamono.netlify.app/)).
- JetBrains: "The zero has a dot inside. The letter 'O' does not" [P] ([jetbrains.com/lp/mono](https://www.jetbrains.com/lp/mono/)).
- The argument against the dot comes from a reader of Hunt's post: a slashed zero "at small sizes ... makes it look less
  like an 8 than the dot in the middle". Hunt's answer concedes the size limit: "I didn't design these fonts for sizes
  so small where this will be an issue" [P] ([comments, Source Code Pro post](https://blog.typekit.com/2012/09/24/source-code-pro/)).
- Lucida Console's history is a natural experiment. In 1993 "A slashed zero was considered, but the designers and
  Microsoft decided that the height difference would be sufficient to distinguish the two characters. However, in a new
  version to be released in 2013, B&H have added the slash to the zero" [P]
  ([Oh, oh, zero!](https://tug.org/TUGboat/tb34-2/tb107bigelow-zero.pdf)). Height difference alone was withdrawn by its
  own designers.
- In a monospaced font "zero cannot be differentiated from Oh by width" through the advance [P] (same paper), but
  designers still narrow the drawing: the zero's ink is 0.95 of the O's at the median, and 0.89–0.92 in Fira Mono,
  Commit Mono, JuliaMono and Cascadia Code [M]. Bigelow cites Wendt (1969) for the "observation that zero narrower than
  Oh is more often interpreted correctly" [P] (same paper).
- The slashed zero has neighbours, which matters for a mathematics user. Bigelow lists the empty set (U+2205), with its
  "slash running northeast to southwest"; the circled division slash, where "the slash does not protrude beyond the rim
  of the circle"; Ø (U+00D8); and theta [P] (same paper).

**`1 l I |`**

- Lucida Sans Typewriter's scheme, in the designer's words: "one upper left serif on ell, two serifs plus upper diagonal
  stroke on numeral one, and four serifs on capital I"; the one differs from the ell "by the shape of the stroke or
  serif at upper left, diagonal on numeral one and horizontal on ell" and by "slightly greater height of ell" [P]
  ([Oh, oh, zero!](https://tug.org/TUGboat/tb34-2/tb107bigelow-zero.pdf)).
- Hunt added a tail to `l` because of feedback from developers using beta fonts in Brackets: "To fully differentiate it
  from the uppercase I, I gave the default glyph for this letter a tail, even though it is uncharacteristic for this
  particular type style" [P] ([Source Sans Pro post](https://blog.typekit.com/2012/08/02/source-sans-pro/)).
- Observed defaults in the 18 faces [M]:
  - `1`: diagonal flag plus a foot on both sides in 17; Iosevka alone has a flag and no foot.
  - `I`: serifs top and bottom in all 18.
  - `l`: top-left serif plus a tail or foot to the right only in 13 (JetBrains Mono, Source Code Pro, Recursive, Commit
    Mono, Intel One Mono, Cascadia Code, Fira Mono, Go Mono, 0xProto, Atkinson Hyperlegible Mono, Maple Mono, JuliaMono,
    Hack); top-left serif plus a flat foot on both sides in 5 (Iosevka, Monaspace Neon, IBM Plex Mono, Geist Mono,
    Departure Mono).
  - `i`: top-left serif plus a foot on both sides in 15; no foot in Source Code Pro and Recursive; a right tail in Hack.
  - The vertical bar: unserifed, running past both the baseline and the capitals (JetBrains Mono: −110 to 830 against
    a cap height of 730).
- Intel One Mono's designers are reported to exaggerate glyph outlines deliberately; that reasoning is only in sources
  I could not open (see Gaps).

**`5 S`, `2 Z`, `8 B`, `6 b`, `g 9 q`**

- No designer in this set explains these pairs beyond listing them (DIN 1450 via Go, above). The renderings show one
  convention everywhere: a flat-topped `5` with a hard corner; a `2` with a round top against a `Z` with a flat top; a
  `B` with a straight spine [M].
- Recursive offers "Simplified 6 and 9" as `ss09`, and a "Simplified 1" as `ss11` [P]
  ([recursive-code-config](https://raw.githubusercontent.com/arrowtype/recursive-code-config/main/config.yaml)).
- For `g`, Lucida's bitmap tests decided the form: "We tried to use the elegant Humanist 'g' with closed lower loop, but
  our bitmap tests showed that the letter shape did not survive at low resolutions and small sizes, so we settled on
  the 'grotesque' style 'g'" [P]
  ([How and Why We Designed Lucida](https://lucidafonts.com/blogs/bigelow-holmes-blog/how-and-why-we-designed-lucida)).
  IBM chose the opposite, for character: "The double decker 'g' ... We adopted this style to make Plex distinctive" [P]
  ([ibm.com/plex/concept](https://www.ibm.com/plex/concept/)).

**`rn m`**

- No designer names this pair. Two devices are visible. Lucida's deep arch join (above) keeps the `n` open at its left
  shoulder. Nine of the 18 faces put a foot serif on `r` (Monaspace Neon, Intel One Mono, IBM Plex Mono, Cascadia Code,
  Fira Mono, Go Mono, 0xProto, Geist Mono, Departure Mono), which widens `r` and plants a mark between the two stems [M].
  With the foot, `r` fills 0.80 of the cell at the median; without it, 0.65 [M].

**Quotes and backtick**

- No designer text. Measured: the straight single quote is a vertical wedge about 106 wide and 308 tall (medians). The
  backtick varies fourfold in area: 210×140 in JetBrains Mono, 283×351 in JuliaMono, 273×305 in Intel One Mono [M].
- Two signs that the small backtick is being abandoned: Monaspace enlarged it from 209×169 in version 1.000 to 272×262
  in 1.400 [M]; JuliaMono, whose default is large, offers `ss07` "smaller grave" for those who want the old form [P]
  ([juliamono.netlify.app](https://juliamono.netlify.app/)).

**Comma, period, colon, semicolon**

- JetBrains: "The comma's shape differs from that of the period, making them easier to tell apart at small sizes. The
  same holds true for derived symbols, as well" [P] ([jetbrains.com/lp/mono](https://www.jetbrains.com/lp/mono/)). Its
  comma is a slanted bar, not a dot with a tail [M].
- Sizes are in section (d).

**`- – — − _ ~`**

- A reader of Hunt's post states the programmer's requirement: the hyphen-minus "should look like a minus sign", with "a
  design that works well with the plus (+) by having the same width and lining up with its crossbar"; another answers
  that "many languages also use the hyphen as a hyphen. There is no great solution" [P]
  ([comments, Source Code Pro post](https://blog.typekit.com/2012/09/24/source-code-pro/)). Hunt himself "adjusted heights
  of dashes and mathematical symbols so that these align better with each other" [P] (same post).
- Measured, the designers split on width [M]. Hyphen-minus as wide as the plus: Source Code Pro (430/430), Cascadia Code
  (488/488), Go Mono (503/503), Iosevka (372/372), Maple Mono (450/470). Hyphen-minus clearly shorter: JetBrains Mono
  (320/470), IBM Plex Mono (290/476), Atkinson (290/502), Monaspace Neon (320/473). Its vertical centre is within 3
  units of the plus's in all 16.
- U+2212 MINUS is within 5% of the plus's width in 13 of 16. JetBrains Mono is the clear exception: its minus is the
  320-unit hyphen [M].
- Underscore: 0.80 of the advance at the median, so two underscores show a gap. A reader of Hunt's post praises exactly
  that: "the distinguishable underscores, so that __ looks like 2 rather than one really long one" [P] (same comments).
  Go Mono and Atkinson Hyperlegible Mono draw it full width, so runs join [M].
- Tilde sits within 22 units of the operator axis in 14 of 16, at about 200 units tall [M].

**Brackets `( [ { <`**

- Input: "Much attention was paid to the size and positioning of symbols frequently used in coding — curly brackets,
  less-than and greater-than signs, the @ sign — characters that can easily be afterthoughts" [P]
  ([input.djr.com/info](https://input.djr.com/info/)).
- Shapes are separated by width as well as form: parenthesis 0.50 of the advance, square bracket 0.49, brace 0.65
  (medians) [M]. Intel One Mono's braces have a visibly exaggerated double wave (`sheets/dis_2.png`) [M].
- Sizes are in section (d).

---

## (d) Punctuation and operators for code

### What the designers say

- **Make punctuation bigger.** Hunt: "In coding, many of the characters we take for granted are more meaningful symbols in
  computer languages. To make these more legible, I increased the size of punctuation marks, and optimized the shapes
  of important characters like the greater- and less-than signs" [P]
  ([Source Code Pro post](https://blog.typekit.com/2012/09/24/source-code-pro/)). Input: "Input's punctuation was designed
  to be large and clear in the context of code" [P] ([input.djr.com/info](https://input.djr.com/info/)).
- **Line operators up.** Go: "punctuation characters easily distinguishable and operators lined up and placed
  consistently" [P] ([Go blog](https://go.dev/blog/go-fonts)). Hunt adjusted the heights of dashes and mathematical
  symbols "so that these align better with each other" [P].
- **Raise the colon when it is an operator.** Intel One Mono: "The colon is automatically raised in operators, to align
  with math symbols"; for other contexts a raised colon can be applied between numbers (`ss11`) or everywhere (`ss12`) [P]
  ([README](https://raw.githubusercontent.com/intel/intel-one-mono/main/README.md)). Commit Mono has a contextual
  colon feature for `:` next to `=`, `<`, `>` and `#` [P]
  ([colon.fea](https://raw.githubusercontent.com/eigilnikolajsen/commit-mono/main/src/features/colon.fea)). Monaspace
  carries `colon.raised` and `period.raised` glyphs [M].
- **The asterisk is contested, and the trend is downward.**
  - Readers told Hunt in 2012 that the raised asterisk was wrong for code: "having *= line up would be great". He
    replied: "I may add an alternate 'splat', but I'm inclined to leave the default as it is" [P]
    ([comments](https://blog.typekit.com/2012/09/24/source-code-pro/)). In the current file (2.042) the asterisk is
    centred 4 units above the plus [M]. So the default was lowered at some point after the post [I].
  - Monaspace moved it too. `cv30` gives an asterisk "vertically aligned closer to the top of the space, similar to how
    the asterisk was in Monaspace 1.0" [P] ([README](https://raw.githubusercontent.com/githubnext/monaspace/main/README.md)).
    Measured: centre 515 in version 1.000, 339 in 1.400, against an axis of 328 [M].
  - Input offers both ("superscripted, or at centered height") [P]; JuliaMono offers a "lighter asterisk" (`ss05`) [P].
- **Iosevka parameterises operator sizes**: `plusSize = 0.52` ("Size of plus and arith symbols"), `operSize = 0.80`,
  `arrowHeight = 1.50`, `symbolMid = 340`, `parenSize = 966` [P]
  ([parameters.toml](https://raw.githubusercontent.com/be5invis/Iosevka/main/params/parameters.toml)).
- **Fira Code retunes Fira Mono's punctuation**: "Some fine-tuning is done for punctuation and frequent letter pairs" [P]
  ([README](https://raw.githubusercontent.com/tonsky/FiraCode/master/README.md)). Measured: the plus is 368 wide in Fira
  Mono 3.206 and 469 in Fira Code 5.002; the hyphen 350 and 401 [M].

### Sizes of `. , : ;` and the quotes [M]

| Font | period ⌀ (w) | period/stem | period/advance | comma height | comma lowest y | colon dots y | colon centre | colon upper-dot centre / x-height | `'` w×h | backtick w×h |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| JetBrains Mono 2.305 | 164 | 1.82 | 0.273 | 306 | -160 | -10..138 ; 412..560 | 275 | 0.88 | 102×300 | 210×140 |
| Source Code Pro 2.042 | 162 | 1.98 | 0.270 | 368 | -213 | -12..157 ; 346..515 | 252 | 0.89 | 110×335 | 200×209 |
| Iosevka 22.1.2 | 156 | 2.00 | 0.312 | 363 | -215 | -8..148 ; 372..528 | 260 | 0.86 | 86×330 | 233×260 |
| Recursive Mono Linear 1.085 | 156 | 1.70 | 0.260 | 371 | -200 | -7..146 ; 386..539 | 266 | 0.87 | 138×305 | 229×295 |
| Monaspace Neon 1.400 | 185 | 1.96 | 0.298 | 384 | -222 | -15..165 ; 374..554 | 270 | 0.90 | 96×332 | 272×262 |
| Commit Mono 1.143 | 154 | 1.83 | 0.257 | 279 | -158 | -8..146 ; 394..548 | 270 | 0.87 | 106×310 | 292×244 |
| Intel One Mono 1.005 | 174 | 2.02 | 0.283 | 284 | -152 | -15..142 ; 322..478 | 232 | 0.86 | 126×305 | 273×305 |
| IBM Plex Mono 2.3 | 148 | 1.85 | 0.247 | 277 | -141 | -9..129 ; 387..525 | 258 | 0.88 | 76×277 | 158×194 |
| Cascadia Code 2407.024 | 145 | 1.40 | 0.247 | 337 | -213 | -10..135 ; 383..527 | 259 | 0.88 | 113×312 | 240×273 |
| Fira Mono 3.206 | 176 | 2.10 | 0.293 | 344 | -179 | -11..151 ; 349..511 | 250 | 0.82 | 106×260 | 230×165 |
| Go Mono 2.010 | 164 | 1.70 | 0.273 | 357 | -193 | 0..164 ; 378..542 | 271 | 0.87 | 145×306 | 217×157 |
| 0xProto 2.502 | 166 | 1.73 | 0.268 | 344 | -193 | 0..150 ; 400..550 | 275 | 0.86 | 126×272 | 231×248 |
| Atkinson Hyperlegible Mono 2.001 | 140 | 1.64 | 0.222 | 272 | -144 | -12..128 ; 375..514 | 251 | 0.90 | 87×239 | 161×135 |
| Geist Mono 1.701 | 124 | 1.48 | 0.207 | 284 | -162 | 0..122 ; 386..508 | 254 | 0.84 | 100×357 | 200×228 |
| Maple Mono 7.800 | 170 | 1.89 | 0.283 | 380 | -224 | -10..160 ; 360..530 | 260 | 0.80 | 90×320 | 280×280 |
| JuliaMono 0.63.2 | 184 | 2.10 | 0.307 | 368 | -195 | 4..188 ; 370..554 | 280 | 0.84 | 137×351 | 283×351 |
| Departure Mono 1.500 | 91 | 1.00 | 0.143 | 273 | -91 | 0..182 ; 364..545 | 273 | 0.83 | 91×273 | 182×182 |
| (ref) Hack 3.003 | 158 | 1.76 | 0.262 | 359 | -189 | 29..194 ; 379..544 | 287 | 0.84 | 85×271 | 234×184 |
| (ref) Roboto Mono 3.001 | 143 | 1.58 | 0.238 | 271 | -164 | -9..128 ; 418..556 | 273 | 0.92 | 78×234 | 194×130 |
| (ref) Inconsolata 3.001 | 115 | 1.64 | 0.230 | 271 | -168 | -11..104 ; 308..423 | 206 | 0.80 | 80×258 | 139×175 |
| (ref) Courier Prime 3.018 | 132 | 1.80 | 0.220 | 287 | -144 | -5..146 ; 305..456 | 226 | 0.84 | 121×271 | 243×184 |

Medians over the 16 designer faces [M]:

- Period: 163 units across, which is **1.84 stems** (range 1.40–2.10) and **0.27 of the advance**. Cascadia Code
  (1.40) and Geist Mono (1.48) are the small-dot outliers; Fira Mono and JuliaMono (2.10) the large.
- Comma: 344 tall, 2.1 times the period, reaching down to −193 (about the descender).
- Colon: the upper dot's top sits 8 units above the x-height, and its centre is at 0.87 of the x-height. Colon and
  period use the same dot.
- The colon's centre is **51 units below the operator axis** at the median (range −95 to +6). That gap is what the
  raised-colon features close. JuliaMono (+6) and Atkinson Hyperlegible Mono (+3) avoid it differently: they put the
  whole operator axis at half the x-height.

### Operators and their axis [M]

| Font | x/2 | cap/2 | axis (`+` centre) | axis/cap | `+` w×h | `-` w | U+2212 w | `=` w | `=` gap/bar | `<` w×h | `*` centre − axis | `~` centre − axis | `:` centre − axis | `->` gap |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| JetBrains Mono 2.305 | 275 | 365 | 330 | 0.452 | 470×470 | 320 | 320 | 430 | 2.00 | 430×530 | 32 | 22 | -55 | 225 |
| Source Code Pro 2.042 | 243 | 328 | 330 | 0.503 | 430×452 | 430 | 430 | 430 | 2.45 | 373×568 | 4 | 0 | -78 | 192 |
| Iosevka 22.1.2 | 260 | 368 | 340 | 0.463 | 372×386 | 372 | 372 | 372 | 1.54 | 392×518 | 276 | -43 | -80 | 108 |
| Recursive Mono Linear 1.085 | 266 | 350 | 300 | 0.429 | 461×461 | 361 | 461 | 461 | 1.88 | 440×568 | 1 | 0 | -34 | 199 |
| Monaspace Neon 1.400 | 257 | 365 | 328 | 0.449 | 473×480 | 320 | 440 | 440 | 2.35 | 435×622 | 11 | -1 | -58 | 248 |
| Commit Mono 1.143 | 270 | 350 | 310 | 0.443 | 468×468 | 388 | 448 | 428 | 1.59 | 404×508 | -6 | 0 | -40 | 214 |
| Intel One Mono 1.005 | 232 | 328 | 327 | 0.499 | 474×480 | 374 | 474 | 428 | 1.72 | 470×484 | 68 | 4 | -95 | 196 |
| IBM Plex Mono 2.3 | 258 | 349 | 305 | 0.437 | 476×486 | 290 | 476 | 476 | 1.94 | 430×578 | 15 | 0 | -47 | 240 |
| Cascadia Code 2407.024 | 259 | 347 | 346 | 0.499 | 488×507 | 488 | 488 | 488 | 1.69 | 468×483 | 4 | 0 | -87 | 120 |
| Fira Mono 3.206 | 264 | 344 | 311 | 0.451 | 368×368 | 350 | 368 | 388 | 1.64 | 425×561 | 19 | 3 | -61 | 213 |
| Go Mono 2.010 | 265 | 361 | 301 | 0.417 | 503×504 | 503 | 503 | 503 | 1.66 | 504×603 | 91 | 0 | -30 | 96 |
| 0xProto 2.502 | 275 | 355 | 307 | 0.432 | 470×502 | 410 | 480 | 470 | 1.35 | 420×586 | -9 | 13 | -32 | 215 |
| Atkinson Hyperlegible Mono 2.001 | 248 | 334 | 248 | 0.371 | 502×496 | 290 | 501 | 501 | 1.43 | 472×491 | 250 | 11 | 3 | 251 |
| Geist Mono 1.701 | 265 | 355 | 295 | 0.415 | 478×478 | 360 | 440 | 440 | 1.65 | 456×512 | 202 | 38 | -41 | 192 |
| Maple Mono 7.800 | 280 | 370 | 330 | 0.446 | 470×470 | 450 | 450 | 450 | 1.67 | 430×480 | 0 | 12 | -70 | 160 |
| JuliaMono 0.63.2 | 275 | 362 | 274 | 0.378 | 465×477 | 412 | 471 | 459 | 1.12 | 462×489 | 1 | -1 | 6 | 144 |
| Departure Mono 1.500 | 273 | 364 | 318 | 0.437 | 455×455 | 273 | 455 | 455 | 1.00 | 364×636 | 182 | 0 | -45 | 363 |
| (ref) Hack 3.003 | 273 | 365 | 313 | 0.429 | 516×517 | 401 | 516 | 516 | 1.37 | 516×489 | 136 | -21 | -26 | 144 |
| (ref) Roboto Mono 3.001 | 264 | 355 | 330 | 0.464 | 487×518 | 374 | 408 | 436 | 1.59 | 414×441 | 141 | -36 | -57 | 207 |
| (ref) Inconsolata 3.001 | 228 | 312 | 314 | 0.504 | 411×419 | 280 | 411 | 411 | 2.39 | 426×520 | 16 | 6 | -108 | 149 |
| (ref) Courier Prime 3.018 | 226 | 290 | 284 | 0.490 | 434×434 | 434 | 434 | 434 | 1.94 | 453×449 | 107 | 0 | -58 | 168 |

- **Where the axis is.** The centre of `+` is at 310 units at the median: 0.445 of the cap height, 0.59 of the
  x-height, and 47 units above half the x-height. Three camps:
  - half the cap height (operators centred on capitals and figures): Source Code Pro 0.503, Cascadia Code 0.499, Intel
    One Mono 0.499;
  - half the x-height (operators centred on lowercase): JuliaMono and Atkinson Hyperlegible Mono;
  - in between: everyone else, 0.42–0.46 of the cap height.
- **One axis for `+ - = < >`.** The centres of hyphen, equals and less-than are within 3 units of the plus's in 14 of 16
  faces, and within 6 in the other two. So `->`, `=>`, `<=`, `>=`, `<-`, `-=` and `+=` line up without any
  substitution [M].
- **Sizes.** The plus is 470 wide (0.78 of the advance) and as tall as wide; its bar is 0.88 of the vertical stem. The
  equals is as wide as the plus, with a gap of 1.66 bar thicknesses (range 1.1–2.5). Less-than and greater-than are
  about 430 wide and 524 tall, 1.15 times the height of the plus.
- **The `->` gap.** The white space between the end of the hyphen and the start of `>` is 198 units at the median (a
  third of a cell), and 96–120 in the three faces with a full-width hyphen (Go Mono, Iosevka, Cascadia Code) [M].
- **Asterisk.** Centred within 32 units of the axis in 11 of 16: JetBrains Mono, Source Code Pro, Recursive, Monaspace
  Neon, Commit Mono, IBM Plex Mono, Cascadia Code, Fira Mono, 0xProto, Maple Mono, JuliaMono. Raised by 68–276 units in
  Intel One Mono, Go Mono, Geist Mono, Atkinson Hyperlegible Mono and Iosevka. Width 478 at the median [M].

### Brackets, bars, underscore, caret [M]

| Font | `(` y-range | `[` y-range | `{` y-range | bar U+007C y-range | `/` y-range | `(` centre − axis | `(` w | `[` w | `{` w | `_` y-range | `_` w | `^` y-range |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| JetBrains Mono 2.305 | -120..840 | -110..830 | -110..830 | -110..830 | -110..830 | 30 | 300 | 245 | 430 | -100..-25 | 480 | 340..730 |
| Source Code Pro 2.042 | -176..732 | -152..708 | -152..708 | -250..750 | -160..710 | -52 | 270 | 277 | 382 | -140..-69 | 480 | 284..670 |
| Iosevka 22.1.2 | -161..841 | -143..823 | -153..833 | -143..823 | -143..823 | 0 | 295 | 276 | 316 | -70..0 | 372 | 450..724 |
| Recursive Mono Linear 1.085 | -141..756 | -148..756 | -161..760 | -161..760 | -130..750 | 7 | 293 | 315 | 442 | -167..-79 | 470 | 367..750 |
| Monaspace Neon 1.400 | -200..801 | -200..801 | -200..801 | -200..801 | -100..730 | -28 | 340 | 328 | 488 | -180..-115 | 530 | 344..765 |
| Commit Mono 1.143 | -170..790 | -170..790 | -170..790 | -170..790 | -170..790 | 0 | 300 | 297 | 429 | -122..-46 | 460 | 378..700 |
| Intel One Mono 1.005 | -147..805 | -135..787 | -139..801 | -100..755 | -100..755 | 2 | 408 | 335 | 473 | -106..-26 | 458 | 271..655 |
| IBM Plex Mono 2.3 | -138..760 | -138..760 | -138..760 | -138..760 | -138..760 | 6 | 289 | 280 | 390 | -169..-95 | 480 | 287..698 |
| Cascadia Code 2407.024 | -98..791 | -104..798 | -104..794 | -151..845 | -93..786 | 1 | 357 | 306 | 361 | -91..0 | 488 | 400..693 |
| Fira Mono 3.206 | -140..840 | -115..815 | -136..836 | -102..807 | -103..809 | 39 | 301 | 251 | 334 | -182..-108 | 500 | 527..840 |
| Go Mono 2.010 | -145..771 | -145..771 | -145..771 | -145..771 | -145..771 | 12 | 323 | 265 | 400 | -72..0 | 600 | 241..723 |
| 0xProto 2.502 | -138..760 | -120..750 | -135..765 | -160..766 | -120..750 | 4 | 335 | 279 | 374 | -86..0 | 486 | 420..750 |
| Atkinson Hyperlegible Mono 2.001 | -162..708 | -162..708 | -162..708 | -162..838 | -90..708 | 25 | 312 | 276 | 343 | -77..0 | 636 | 311..668 |
| Geist Mono 1.701 | -110..750 | -110..750 | -120..750 | -110..750 | -110..750 | 25 | 280 | 320 | 380 | -78..0 | 440 | 373..710 |
| Maple Mono 7.800 | -172..855 | -165..865 | -165..865 | -130..810 | -130..830 | 11 | 320 | 300 | 430 | -165..-75 | 450 | 320..670 |
| JuliaMono 0.63.2 | -243..838 | -209..838 | -203..846 | -264..884 | -190..775 | 24 | 298 | 290 | 385 | -20..66 | 486 | 326..745 |
| Departure Mono 1.500 | -91..818 | -91..818 | -91..818 | -91..818 | -91..818 | 46 | 273 | 273 | 455 | 0..91 | 455 | 545..727 |
| (ref) Hack 3.003 | -132..759 | -132..799 | -124..799 | -236..764 | -93..729 | 0 | 224 | 305 | 413 | -151..-93 | 510 | 457..729 |
| (ref) Roboto Mono 3.001 | -229..802 | -152..812 | -179..780 | -194..711 | -61..711 | -44 | 258 | 193 | 330 | -74..0 | 448 | 331..711 |
| (ref) Inconsolata 3.001 | -104..735 | -89..670 | -95..701 | -151..652 | -42..665 | 2 | 292 | 287 | 355 | -80..-19 | 431 | 343..623 |
| (ref) Courier Prime 3.018 | -167..674 | -163..670 | -163..670 | -173..681 | -173..681 | -31 | 277 | 264 | 397 | -189..-123 | 627 | 245..590 |

- The three bracket pairs share one vertical extent within a face: identical in 5 of 16, and within 25 units in 15.
  Median parenthesis: from −146 to 790, **934 units tall**, centred 6 units above the operator axis [M].
- The brackets' top is 83 units above the cap height and 44 above the ascender; their bottom is 51 units short of the
  descender (medians) [M]. So brackets enclose capitals and ascenders fully and descenders partly.
- The vertical bar has exactly the square bracket's extent in 7 of 16 [M].
- Underscore: 0.80 of the advance, as thick as the hyphen, with its top at −26 at the median [M].
- Caret: a large chevron in the upper half, from about 340 to the cap height [M].

---

## (e) Ligatures: positions for and against, and the alternatives

### For

- **Fira Code (Nikita Prokopov).** "For the human brain, sequences like `->`, `<=`, or `:=` are single logical tokens,
  even if they take two or three characters on the screen. Your eye spends a non-zero amount of energy to scan, parse
  and join multiple characters into a single logical one." Ligatures are "just a font rendering feature: underlying
  code remains ASCII-compatible. This helps to read and understand code faster" [P]
  ([README](https://raw.githubusercontent.com/tonsky/FiraCode/master/README.md)). No measurement is cited.
- **JetBrains Mono** gives two purposes: "To reduce noise by merging symbols and removing details so the eyes are
  processing less" and "To balance whitespace more efficiently by shifting the glyphs in certain cases" [P]
  ([jetbrains.com/lp/mono](https://www.jetbrains.com/lp/mono/)). It ships "JetBrains Mono NL, which doesn't include any
  ligatures" [P] ([README](https://raw.githubusercontent.com/JetBrains/JetBrainsMono/master/README.md)).
- **Cascadia Code**: ligatures help "make code more readable and user-friendly for some people"; Cascadia Mono is the
  same design without them [P] ([Microsoft devblog](https://devblogs.microsoft.com/commandline/cascadia-code/),
  [README](https://raw.githubusercontent.com/microsoft/cascadia-code/main/README.md)).
- **Berkeley Mono**: "We offer 150+ ligatures for people that like them ... And for the purists out there, we also offer
  a version without ligatures for those who prefer utmost explicitness in their code" [P]
  ([usgraphics.com](https://usgraphics.com/products/berkeley-mono)).

### Against

- **Matthew Butterick (Triplicate).** "Ligatures in programming fonts are a terrible idea." Two arguments [P]
  ([essay, 2019](https://practicaltypography.com/ligatures-in-programming-fonts-hell-no.html)):
  - they contradict Unicode: on seeing ≠, "Are you looking at a != ligature that's shaped like ≠? Or the actual Unicode
    character 0x2260";
  - "ligature substitution is 'dumb' in the sense that it only considers whether certain characters appear in a certain
    order. It's not aware of the semantic context. Therefore, any global ligature substitution is guaranteed to be
    semantically wrong part of the time."

  His summary: redesigning a character to disambiguate it is fine, "Whereas ligatures are going the opposite direction:
  making distinct characters appear to be others." On Triplicate: "there are no programming ligatures in Triplicate, and
  there never will be" [P] ([Triplicate](https://practicaltypography.com/triplicate.html)).
- **JuliaMono (cormullion).** "I'm not a fan of their use in coding fonts ... I like to see exactly what I've typed,
  rather than what the font has decided to replace it with." And on the speed claim: "I don't quite agree with Fira
  Code's developer that they save your brain some milliseconds of recognition time; I find I have to double-check a
  combination to remember what it represents, or how many characters have been replaced" [P]
  ([juliamono.netlify.app](https://juliamono.netlify.app/)).
- **0xProto.** "ligatures that alter the original meaning do not truly fit the definition", and distorted ligatures "make
  it challenging to anticipate their meaning if any part of the string is erased". 0xProto abstains "from using
  ligatures that modify both meaning and form" [P]
  ([README](https://raw.githubusercontent.com/0xType/0xProto/main/README.md)).

### The middle positions, which are the useful ones

- **Opt-in, grouped, off by default.**
  - Intel One Mono: "Programming ligatures are not active by default"; they are behind `ss01`, with `<=`/`>=` arrow forms
    behind `ss02` [P] ([README](https://raw.githubusercontent.com/intel/intel-one-mono/main/README.md)).
  - Commit Mono: its few ligatures "provide additional functionality (i.e. != becomes ≠), but they are off by default",
    and it "won't be updated with ligatures that purely serve aesthetic purposes" [P] ([commitmono.com](https://commitmono.com/)).
  - MonoLisa: "We know coding ligatures are a divisive topic ... By default, MonoLisa only enables whitespace ligatures —
    subtle adjustments that improve readability without changing the meaning of your code. All other coding ligatures
    are opt-in" [P] ([monolisa.dev](https://www.monolisa.dev/)).
  - Monaspace: ten groups in `ss01`–`ss10`, by language; `liga` only "enables customized spacing of repeating characters,
    like `///` or `||`" and is "designed to avoid activating inside longer sequences like `////`" [P]
    ([README](https://raw.githubusercontent.com/githubnext/monaspace/main/README.md)).
  - Iosevka: ligation is in `calt`, "though not all of them are enabled by default", with per-language sets and three
    spacings: Default, Term ("Arrows and geometric symbols will become narrower") and Fixed (no ligation) [P]
    ([README](https://raw.githubusercontent.com/be5invis/Iosevka/main/README.md),
    [custom-build.md](https://raw.githubusercontent.com/be5invis/Iosevka/main/doc/custom-build.md),
    [parameters.toml](https://raw.githubusercontent.com/be5invis/Iosevka/main/params/parameters.toml)).
- **Cell-preserving joins.** JuliaMono applies eight substitutions under `calt` (`->`, `=>`, `|>`, `<|`, `::`, `<--`, `-->`,
  `<-->`) and states the rule: "the substitute glyphs occupy the same width as the source glyphs they're replacing",
  because a Unicode arrow is "the width of a single character" and would change the line length [P]
  ([juliamono.netlify.app](https://juliamono.netlify.app/)). These are joins and alignments, not new symbols.
- **Contextual alignment instead of substitution.** Intel's raised colon, Commit Mono's case-sensitive punctuation,
  Monaspace's repeat spacing and MonoLisa's "whitespace ligatures" (all above). None changes which characters the
  reader sees.
- **Texture healing and smart kerning** (section b) are the same idea applied to letters.
- **Two cautions from designers about contextual features.** Monaspace's optional `[]` ligature "can be distracting when
  authoring arrays in many editors, because they automatically insert the closing bracket" [P]
  ([README](https://raw.githubusercontent.com/githubnext/monaspace/main/README.md)). JuliaMono: "these ligatures have to
  be interpreted by the terminal you're using ... Not all terminals support ligatures" [P]
  ([juliamono.netlify.app](https://juliamono.netlify.app/)).

---

## (f) What they measured or tested with users

Stated plainly: **no designer in this set publishes a controlled measurement of reading speed, error rate or
preference for their code face.** What exists:

| Face | What was done | What was reported | Source |
|---|---|---|---|
| Intel One Mono | "A panel of low-vision and legally blind developers provided feedback at each stage of design" | Goals named (fatigue, eyestrain, coding errors); no numbers and no protocol | [P] [README](https://raw.githubusercontent.com/intel/intel-one-mono/main/README.md) |
| Source Sans / Source Code Pro | Beta fonts shipped in Brackets; developers sent recommendations | The tailed `l` "came about due to user feedback"; punctuation and operator adjustments "came from input we received from working closely with the Brackets team" | [P] [Source Sans post](https://blog.typekit.com/2012/08/02/source-sans-pro/), [Source Code post](https://blog.typekit.com/2012/09/24/source-code-pro/) |
| Lucida | "experiments with hand-edited bitmap renderings of letters at various resolutions"; spacing tuned to the contrast sensitivity function | "The x-height always seemed most important for letter recognition"; the two-storey `g` failed the bitmap tests; 5–7 cycles per degree at 16 inches; "the jury is still out" on spacing | [P] [How and Why We Designed Lucida](https://lucidafonts.com/blogs/bigelow-holmes-blog/how-and-why-we-designed-lucida) |
| Go fonts | "tested for technical uses, particularly programming" (no detail); design justified by cited studies | Cites Morris et al. 2002 (serifs slow reading only at very small sizes), Reimer et al. 2014 (humanist over grotesque), Legge & Bigelow 2011 (x-height), DIN 1450 | [P] [Go blog](https://go.dev/blog/go-fonts) |
| Zero and O | Literature review by a designer | Wendt 1969: a zero narrower than O "is more often interpreted correctly"; Kerpelman 1969: business programmers "favor marking the zero", scientific programmers the letter | [P] [Oh, oh, zero!](https://tug.org/TUGboat/tb34-2/tb107bigelow-zero.pdf) |
| Commit Mono | A survey, beta testers and an interview are thanked | No results published; the site has a "Guess the Character" game for visitors | [P] [commitmono.com](https://commitmono.com/) |
| Recursive | Dogfooding: "it was used to write Python scripts to automate type production work ... Through this active usage, Recursive Mono was crafted" | Advice: weight 400 for light text on dark, "adjust the weight upwards to 500" for dark on light | [P] [README](https://raw.githubusercontent.com/arrowtype/recursive/main/README.md) |
| Berkeley Mono | "has written production code during its entire development cycle" | None | [P] [usgraphics.com](https://usgraphics.com/products/berkeley-mono) |
| Operator Mono | A journalist showed it to one developer | He misread the italic: "the 'ref' attribute ... looked, at first glance, like 'rel'", because of the cursive `f` | [S] [Wired](https://www.wired.com/2016/02/hoefler-co-s-new-typewriter-inspired-font-is-crafted-for-coders) |
| Input | Seven weights justified by rendering differences | "Changing between Input's finely-grained weights can counteract the halo effect of light type on a dark background" | [P] [input.djr.com/info](https://input.djr.com/info/) |
| Commit Mono | The same point, as a number | "Recommended weight: 400 for dark mode, 450 for light mode" | [P] [commitmono.com](https://commitmono.com/) |

Claims to treat as hypotheses, because each is a designer's statement with no data attached [P]:

- Fira Code: "helps to read and understand code faster".
- Commit Mono: smart kerning is "improving reading speed and accuracy".
- JetBrains Mono: "The easier the forms, the faster the eye perceives them"; a 9° italic "maintains the optimal contrast".
- MonoLisa: wider forms create "less eye strain over long periods of time".

---

## What this means for our font

Values are per 1000-unit em. Each line says what it rests on. Where I chose between camps, that is marked [I].

### Proportions

| Parameter | Recommended | Basis |
|---|---:|---|
| Units per em | 1000 | Convention; every number here translates directly |
| Advance | **600** | Hunt's "standard monowidth of 60%"; 10 of 16 measured; Courier-compatible (Go); pairs 1:2 with CJK at 1200 (Maple) |
| x-height | **530** | Lucida and Go state 53%; measured median 528. It stays under JetBrains's 550, where Hunt's "overly condensed" warning starts to apply [I] |
| Cap height | **700** | Median 705; gives x/cap = 0.757 (median 0.746) |
| Ascender | **740** | Median 740; 40 above the capitals, Lucida's rule for `l` against `I` and for quieter acronyms |
| Descender | **−200** | Median −198 |
| Figure height | **700** (cap height) | 14 of 16. Source Code Pro's shorter figures are a reasoned minority; zero is distinguished by its mark and width instead |
| Overshoot of rounds | 10–12 | Measured median 11 |
| Vertical stem, Regular | **86** | Median 87; x-height/stem = 6.2 (median 6.0, Lucida 5.5) |
| Horizontal stroke | **78** (0.90 of vertical) | Median ratio 0.90 |
| Stem at Bold (700) | **129** (1.5×) | Go states 1.5×; measured median about 1.5; stem/advance 0.215, inside the measured 0.20–0.25 band |
| Stem at Light (300) | **60** (0.70×) | Measured weight-300 stems run 45–79, median about 61 |
| Default line height | **1.25** | Iosevka 1.25; JetBrains and Input say 1.2; measured median 1.253 |
| hhea and typo metrics | ascender 980, descender −270, gap 0 | Sums to 1250. Set `USE_TYPO_METRICS` (13 of 16 do) and make the win metrics agree, so every platform gives the same line |
| Italic angle | **10°** | Median 10°; JetBrains argues for 9°, Monaspace and Source Code Pro use 11° |

Weight axis: 300 to 700 covers what developers are told to use (Recursive: 400 on dark, 500 on light; Commit Mono: 400
and 450). Extending to 200 and 800 matches Monaspace [P][M]. The period, the dots and the comma need their own
interpolation schedule; they are not a fixed multiple of the stem (JetBrains: 2.9 stems at Thin, 1.5 at Bold) [M].

### Fitting letters to the cell

- **Target ink widths**, as fractions of the 600 advance: `n` 0.70 (420), `o` 0.78 (side bearing 64), `H` 0.74, `m` 0.83
  (500), `w` 0.90, `M` 0.80, `W` 0.93, `@` 0.88, `0` 0.80, `O` 0.84 [M medians].
- **Narrow letters filled to 0.70–0.78**: `i` 0.72, `l` 0.77, `1` 0.74, `I` 0.69, `f` 0.79, `t` 0.78, `r` 0.73, `j` 0.61.
  Add structure only "in areas that would seem like empty gaps otherwise" (Hunt) [P][M].
- **Side bearings**: `n` 93 left and 89 right (sum 182, which is 0.76 of a 240-unit counter); `o` 64 each side. The
  kernel can compute the ratio of inter-letter gap to counter for every lowercase pair; hold it near 0.75 [M][I].
- **`m`**: thin the stems to about 0.91 of the `n` stem (78), the middle one a little more (JetBrains 84/74/84). Its
  counters will be about half of `n`'s; that is normal for the genre [M].
- **Deepen the arch joins** of `n`, `m`, `h`, `r`, `u` (Lucida). It protects `n` against `o` and `rn` against `m` at
  small sizes [P].
- **Squarish rounds** are a legitimate way to enlarge counters at 0.6 em (JetBrains; Input's "straight sides") [P].
  Treat it as a style parameter of the kernel, for example a superellipse exponent, and judge it by counter area [I].

### The disambiguation set, as defaults

| Glyphs | Default form | Basis |
|---|---|---|
| `0` | Forward slash kept **inside** the oval, ink 0.95 of `O`'s width. Alternates through `zero` and a `cv`: dotted, plain | 10 of 18 use a slash; Lucida Console added the slash in 2013; the dot "looks like an 8" at small sizes (Hunt thread). Keeping the slash inside the rim separates it from ∅ and Ø [I, from Bigelow's descriptions] |
| `O` | Unmarked, wider and rounder than `0` | "the numeral gets modified, not the letter" (Bigelow) |
| `1` | Diagonal flag + flat foot on both sides | 17 of 18 |
| `l` | Horizontal top-left serif + tail curving right, at ascender height (above `1` and `I`) | 13 of 18; Hunt's user feedback; Lucida's height rule |
| `I` | Serifs top and bottom | 18 of 18 |
| U+007C | Plain bar on the bracket extent, no serifs | Measured convention |
| `i` `j` | Top-left serif; `i` with a foot on both sides | 15 of 18; fills the cell to 0.72 |
| `r` | Decide by test: bare `r` at 0.65–0.70 with a deep arch, or footed `r` at 0.80 | 9 of 18 use the foot; it guards `rn` [M][I] |
| `5`/`S`, `2`/`Z`, `8`/`B` | Flat top and hard corner on `5`; round-top `2` against flat-top `Z`; straight spine on `B` | DIN 1450 pairs (via Go); universal in the renderings |
| `6`/`b`, `9`/`g`/`q` | Curved terminals on `6` and `9`; single-storey `g` with an open hook; plain straight `q` | Lucida's bitmap finding for `g`; Recursive keeps a simplified `6 9` as an option |
| `'` `"` | Straight vertical wedges, about 105×300, hanging from cap height | Medians |
| Backtick | Large and steep: at least 240×250, at a clearly different angle from `'` | Median 230×246; Monaspace enlarged its own; JuliaMono's default is large |
| `.` | 160 units across (1.86 stems, 0.27 of the advance) | Medians; Hunt and Ross both ask for large punctuation |
| `,` | Not a dot with a tail: a distinct slanted stroke, 340 tall, down to −190 | JetBrains's rule; medians |
| `:` `;` | Same dot as the period; top of the upper dot at x-height + 8 | Medians |

### Operators and brackets

- **One axis for `+ - = < > ~ *` and the arrows: y = 310** (0.44 of the cap height, 45 above half the x-height). This is
  the measured middle camp and serves both lowercase identifiers and capitals or figures [M][I]. Expose it as a single
  kernel parameter, as Iosevka does with `symbolMid`.
- **Hyphen-minus drawn as a minus**: the same width as the plus (470, x from 65 to 535) and the same bar thickness (76).
  Source Code Pro, Cascadia Code, Go Mono and Iosevka do this; in code and mathematics the minus reading dominates
  [M][I]. Make U+2212 identical, U+2010 a short hyphen (about 290), the en dash 475 and the em dash 600, touching both
  edges (measured medians for the dashes) [M].
- **Plus** 470×470; **equals** 470 wide with a gap of 1.7 bars; **less and greater** 430 wide and 530 tall, on the same
  centre. With these, the white gap inside `->` and `=>` is 65 + 85 = 150 units, a quarter of a cell, with no
  ligature [derived from M].
- **Asterisk on the axis**, about 470 wide, with a raised form as a `cv` alternate. Two families moved theirs down after
  release [M][P].
- **Tilde on the axis**, about 215 tall. **Caret** as a large chevron from about 340 to 715 (medians) [M].
- **Colon**: by default on the baseline with the period. A `calt` rule raises it by about 40 units next to `=`, `:`,
  `<`, `>` and `-`, as Intel One Mono, Commit Mono and Monaspace do [P].
- **Brackets**: one extent for `( ) [ ] { }` and the bar: **−150 to 790** (940 tall, centred at 320). Widths:
  parenthesis 300, square bracket 285, brace 390, so the three differ in width as well as shape (medians) [M]. Offer a
  straighter brace as an alternate only if tests ask for it, as Input does [P].
- **Underscore**: 480 wide, so the gaps show in `__`; as thick as the hyphen; top at about −30 [M]. For Python dunders
  the visible gap lets the eye count [I].
- **Box drawing** must use the full 1250 line and the 600 advance exactly. None of the sources above discusses it, so
  its rules should come from the terminal-rendering research, not from this report.

### Ligatures and contextual features

1. **Ship no symbol-replacing ligatures by default.** Nobody answers the semantic objection (Butterick), the speed claim
   (Fira Code) is unmeasured, and the newer designs have moved to opt-in (Intel, Commit, MonoLisa, Monaspace) [P].
2. **Put cell-preserving alignment in `calt`**: the raised colon in operators, punctuation shifted next to capitals, even
   spacing of `//`, `..` and `||`. These never change which characters the reader sees [P].
3. **Offer joins as stylistic sets**, each keeping one cell per character and each component recognisable (JuliaMono's
   width rule, 0xProto's "don't deform shape"): `->`, `=>`, `<-`, `|>`, `::`, `<=`, `>=`, `!=` drawn as aligned pairs,
   not as →, ⇒, ≤, ≠ [P][I].
4. **Build a no-features variant** for terminals and editors that cannot switch features, as JetBrains Mono NL, Cascadia
   Mono, Iosevka Fixed and 0xProto NL do [P].
5. **Make texture healing opt-in, and generate it.** Because our glyphs come from parameters, `.left`, `.right` and
   `.both` variants can be computed instead of drawn. Start with Commit Mono's safer form: shift by up to 44 units,
   shapes unchanged, never past the cell edge. Add Monaspace-style widening only if tests show a gain, and cap it at
   the cell edge; Monaspace's `m.both` and `w.both` overhang by 2 and 44 units, which a cell-grid terminal may clip
   [M][I]. The default glyphs must already give an even texture, because terminals often do not apply `calt` (JuliaMono) [P].

### What to measure ourselves, since nobody has

- Confusion rates for the pairs in section (c) at 9–14 px: slashed against dotted zero, tailed against footed `l`,
  bare against footed `r`.
- Texture evenness as a number: the variance of white-gap widths along rendered words, default against healed.
- Whether the operator axis reads better at 310 or at half the cap height (350) in `x-1`, `N-1`, `a->b`, `A=>B`.

---

## Disagreements between sources

- **x-height.** JetBrains maximises it (550) and says more pixels per letter help. Hunt says a very large x-height at
  fixed width makes letters "overly condensed" and monotonous, and uses 486. Both ship at a 600 advance [P][M].
- **Zero.** Dot (Hunt, JetBrains, Monaspace, Plex) against slash (Bigelow's later practice, Intel, Go, Iosevka). The one
  stated argument is against the dot at small sizes [P].
- **Ligatures.** Fira Code and JetBrains say they reduce effort; Butterick, JuliaMono and 0xProto say they misrepresent
  code. Neither side cites a measurement [P].
- **Asterisk height.** Hunt in 2012 defended the raised asterisk as the default; his own font and Monaspace now centre it [P][M].
- **Hyphen-minus width.** As wide as the plus (Source Code Pro, Cascadia, Go, Iosevka) or a short hyphen (JetBrains,
  Plex, Atkinson, Monaspace 1.4) [M].
- **Advance.** 0.60 is "standard" (Hunt). MonoLisa, Monaspace, 0xProto, Intel and Atkinson go 2–7% wider for openness;
  Iosevka goes to 0.50 for density [P][M].
- **Proportional fonts for code.** Ross argues the editor should do the alignment and offers Input Sans. Hunt calls
  monospacing "a very useful convention". Clymer says "It's just easier to navigate through the code if things line up" [P][S].
- **Operator axis.** Half the cap height (Source Code Pro, Cascadia, Intel), half the x-height (JuliaMono, Atkinson) or
  between (the rest) [M].

## Gaps

- Hoefler&Co's "Introducing Operator" post and Frere-Jones Type's Intel One Mono write-up could not be read (a
  script-rendered page; HTTP 403). Fast Company's and VML's accounts of the Intel panel were also blocked. The claims
  that testers confused `x`/`y` and `e`/`c`, and Frere-Jones's defence of the braces, appeared only in search-result
  summaries and are not used above.
- No font files were measured for Input, Berkeley Mono, Operator Mono, MonoLisa, Triplicate, Lucida Console, Consolas
  or SF Mono (commercial licences).
- Aaron Bell's own reasoning for Cascadia Code's proportions was not found in the README or the launch post.
- Geist Mono, Atkinson Hyperlegible Mono, IBM Plex Mono and Fira Mono publish almost no mono-specific rationale; they are
  represented here by measurements.
- DIN 1450 itself was not read; it is cited through Bigelow.
- Iosevka was measured at version 22.1.2 (the build served by Fontsource); its metrics match the current parameter file.
- No source discusses box-drawing design or how line height interacts with terminal cell rounding.

## Appendix: fonts measured

| Face | Version in file | Source of the file |
|---|---|---|
| JetBrains Mono | 2.305 | https://raw.githubusercontent.com/JetBrains/JetBrainsMono/master/fonts/ttf/JetBrainsMono-Regular.ttf |
| Source Code Pro | 2.042 | https://raw.githubusercontent.com/adobe-fonts/source-code-pro/release/TTF/SourceCodePro-Regular.ttf |
| Iosevka | 22.1.2 | https://cdn.jsdelivr.net/fontsource/fonts/iosevka@latest/latin-400-normal.ttf |
| Recursive (MONO=1, CASL=0, wght=400) | 1.085 | https://raw.githubusercontent.com/google/fonts/main/ofl/recursive/ (variable TTF) |
| Monaspace Neon | 1.400, and 1.000 for comparison | https://raw.githubusercontent.com/githubnext/monaspace/main/fonts/Static%20Fonts/Monaspace%20Neon/MonaspaceNeon-Regular.otf and tag v1.000, `fonts/otf/` |
| Commit Mono | 1.143 | https://cdn.jsdelivr.net/gh/eigilnikolajsen/commit-mono@main/src/fonts/fontlab/CommitMonoV143-400Regular.otf |
| Intel One Mono | 1.005 (Latin subset) | https://cdn.jsdelivr.net/fontsource/fonts/intel-one-mono@latest/latin-400-normal.ttf |
| IBM Plex Mono | 2.3 | https://raw.githubusercontent.com/google/fonts/main/ofl/ibmplexmono/IBMPlexMono-Regular.ttf |
| Cascadia Code (wght=400) | 2407.024 | https://raw.githubusercontent.com/google/fonts/main/ofl/cascadiacode/ (variable TTF) |
| Fira Mono | 3.206 | https://raw.githubusercontent.com/mozilla/Fira/master/ttf/FiraMono-Regular.ttf |
| Fira Code | 5.002 (Latin subset) | https://cdn.jsdelivr.net/fontsource/fonts/fira-code@latest/latin-400-normal.ttf |
| Go Mono | 2.010 | https://raw.githubusercontent.com/golang/image/master/font/gofont/ttfs/Go-Mono.ttf |
| 0xProto | 2.502 | https://raw.githubusercontent.com/0xType/0xProto/main/fonts/0xProto-Regular.ttf |
| Atkinson Hyperlegible Mono (wght=400) | 2.001 | https://raw.githubusercontent.com/google/fonts/main/ofl/atkinsonhyperlegiblemono/ (variable TTF) |
| Geist Mono (wght=400) | 1.701 | https://raw.githubusercontent.com/google/fonts/main/ofl/geistmono/ (variable TTF) |
| Maple Mono | 7.800 (Latin subset) | https://cdn.jsdelivr.net/fontsource/fonts/maple-mono@latest/latin-400-normal.ttf |
| JuliaMono | 0.63.2 | https://raw.githubusercontent.com/cormullion/juliamono/master/JuliaMono-Regular.ttf |
| Departure Mono | 1.500 | https://cdn.jsdelivr.net/gh/rektdeckard/departure-mono@main/public/assets/DepartureMono-Regular.otf |
| Hack, Roboto Mono, Inconsolata, Courier Prime | 3.003, 3.001, 3.001, 3.018 | source-foundry/Hack and google/fonts on raw.githubusercontent.com |

Method notes:

- x-height, cap height, ascender and descender are the bounding-box extremes of `x`, `H`, `h` and `p`.
- Stems are the widths of the filled spans on a horizontal scan-line through `n` at a quarter of the x-height. The
  horizontal stroke is taken from a vertical scan-line through the bar of `H`.
- The "operator axis" is the vertical centre of the bounding box of `+`.
- "Line height (hhea)" is (ascent − descent + lineGap) / em from the `hhea` table. Platforms that use the `OS/2` win
  metrics will differ for some fonts: JetBrains Mono is 1.32 by hhea and 1.565 by win metrics.
- Zero forms were classified from the contours of the default `0` glyph and confirmed on the renderings. Feet and tails
  on `r`, `l`, `i`, `1` were classified from a scan-line 20 units above the baseline.
- Weights other than Regular, and italics, were measured from the same repositories' static files or by instancing the
  variable fonts along `wght`.
