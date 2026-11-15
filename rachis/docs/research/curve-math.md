# The mathematics for the outline kernel

Research report, 2026-11-15. Scope: Hobby's splines as METAFONT implements them, the penpos/penstroke model and Computer Modern's joins, superellipse quadrants as single cubics, offset (parallel) curves, rules for clean outlines and the cubic-to-quadratic conversion, and what Iosevka, MetaType1, MetaFog, mf2pt1 and Metapolator report about programmatic fonts.

## How to read this report

- Every claim carries its source link. A claim marked **[measured]** is a number I computed in this session; the scripts are listed in the last section and can be rerun. A claim marked **[inference]** is my own reasoning from the sources.
- Lengths in measurements are font units at 1000 units per em.
- No TeX, METAFONT or MetaPost binary is installed here and a system install was refused, so the Hobby implementation was verified against two published vectors and against an independent port of MetaPost's `mp_make_choices` (details in section (a)).

---

## (a) Hobby's algorithm, complete enough to implement and test

Sources read in full: Hobby's paper ([Discrete Comput. Geom. 1 (1986) 123-140](https://link.springer.com/content/pdf/10.1007/BF02187690.pdf)); `mf.web` section 116 (`velocity`) and part 18 "Choosing control points" ([mf.web](https://raw.githubusercontent.com/TeX-Live/texlive-source/trunk/texk/web2c/mf.web)); The METAFONTbook chapter 14 ([mfbook.tex](https://mirrors.ctan.org/systems/knuth/dist/mf/mfbook.tex)).

### a.1 Notation

Knots are complex numbers `z_0 … z_n`. For the segment from `z_k` to `z_{k+1}`:

- `δ_k = z_{k+1} − z_k`, `d_k = |δ_k|` (must be nonzero);
- turning angle at an interior knot `ψ_k = arg(δ_k / δ_{k−1})`, taken in `[−180°, 180°]`; for an open path `ψ_n = 0`;
- `θ_k` is the angle from the chord `δ_k` to the outgoing direction at `z_k`; `φ_k` is the angle from the incoming direction at `z_k` to the chord `δ_{k−1}`. A smooth knot satisfies `θ_k + φ_k + ψ_k = 0` ([mf.web §273](https://raw.githubusercontent.com/TeX-Live/texlive-source/trunk/texk/web2c/mf.web); METAFONTbook eq. (∗));
- tensions: `τ_k` leaving `z_k`, `τ̄_{k+1}` entering `z_{k+1}`; `α_k = 1/τ_k`, `β_{k+1} = 1/τ̄_{k+1}`. Default tension is 1. METAFONT requires tension ≥ 3/4 ([METAFONTbook ch. 14](https://mirrors.ctan.org/systems/knuth/dist/mf/mfbook.tex)); Hobby's theorem needs only `τ > 2/3` ([paper, Theorem 1](https://link.springer.com/content/pdf/10.1007/BF02187690.pdf)).

### a.2 Preparation rules (METAFONT's, from chapter 14 and `make_choices`)

1. Two consecutive equal knots are joined by an explicit degenerate curve whose control points equal the knots; the neighbouring sides become `curl 1` ([mf.web §271](https://raw.githubusercontent.com/TeX-Live/texlive-source/trunk/texk/web2c/mf.web)).
2. An empty direction specifier at the start or end of a path, or next to `&`, means `{curl 1}`. A direction given on one side of a knot is copied to the other side. A knot next to explicit control points inherits the direction of that segment ([METAFONTbook ch. 14](https://mirrors.ctan.org/systems/knuth/dist/mf/mfbook.tex)).
3. A knot whose direction is specified in any way is a **breakpoint**. "A path decomposes into independent segments at 'breakpoint' knots" ([mf.web §269](https://raw.githubusercontent.com/TeX-Live/texlive-source/trunk/texk/web2c/mf.web)). Each run between breakpoints is solved alone. A cycle with no breakpoint is solved as a cyclic system.
4. Plain METAFONT's operators are macros: `--` is `{curl 1}..{curl 1}`, `---` is `..tension infinity..` with `infinity = 4095.99998`, `...` is `..tension atleast 1..` ([plain.mf](https://mirrors.ctan.org/systems/knuth/dist/lib/plain.mf)).

### a.3 The linear system for the angles

Unknowns: `θ_0 … θ_n` (open) or `θ_0 … θ_{n−1}` (cycle). Then `φ_k = −ψ_k − θ_k`.

**Interior knot** `0 < k < n` (every knot of a cycle, indices mod n). Equal mock curvature on both sides gives ([mf.web §276](https://raw.githubusercontent.com/TeX-Live/texlive-source/trunk/texk/web2c/mf.web)):

```
A_k θ_{k−1} + (B_k + C_k) θ_k + D_k θ_{k+1} = −B_k ψ_k − D_k ψ_{k+1}

A_k = α_{k−1} / (β_k² d_{k−1})        B_k = (3 − α_{k−1}) / (β_k² d_{k−1})
C_k = (3 − β_{k+1}) / (α_k² d_k)      D_k = β_{k+1} / (α_k² d_k)
```

With all tensions 1 this is

```
θ_{k−1}/d_{k−1} + 2 (1/d_{k−1} + 1/d_k) θ_k + θ_{k+1}/d_k = −2 ψ_k/d_{k−1} − ψ_{k+1}/d_k
```

**Start of an open run** ([mf.web §277, §294-296](https://raw.githubusercontent.com/TeX-Live/texlive-source/trunk/texk/web2c/mf.web)):

- given direction `w_0`: `θ_0 = arg(w_0) − arg(δ_0)`, reduced into `[−180°, 180°]`;
- curl `γ_0`: `θ_0 + u_0 θ_1 = −u_0 ψ_1`, with
  `u_0 = min(4, ((3 − α_0) α_0² γ_0 + β_1³) / (α_0³ γ_0 + (3 − β_1) β_1²))`;
  with tensions 1 this is `u_0 = (2γ_0 + 1)/(γ_0 + 2)`. The cap at 4 is METAFONT's `curl_ratio`.

**End of an open run**:

- given direction `w_n`: `θ_n = arg(w_n) − arg(δ_{n−1})` (and `φ_n = −θ_n`);
- curl `γ_n`: `f_n θ_{n−1} + θ_n = 0`, with
  `f_n = min(4, ((3 − β_n) β_n² γ_n + α_{n−1}³) / (β_n³ γ_n + (3 − α_{n−1}) α_{n−1}²))`.

**Special case**: one segment with a curl at both ends is a straight line with control points `z_0 + δ_0/(3τ_0)` and `z_1 − δ_0/(3τ̄_1)` ([mf.web §302](https://raw.githubusercontent.com/TeX-Live/texlive-source/trunk/texk/web2c/mf.web)). The linear system is singular there when `γ_0 γ_1 = 1`, which the METAFONTbook names as the only exception to uniqueness.

**Solving.** The open system is tridiagonal. METAFONT eliminates forward into `θ_k + u_k θ_{k+1} = v_k + w_k θ_0` and substitutes back; for a cycle it starts with `u_0 = v_0 = 0, w_0 = 1` and closes with `θ_n = θ_0` ([mf.web §273-286](https://raw.githubusercontent.com/TeX-Live/texlive-source/trunk/texk/web2c/mf.web)). The system is diagonally dominant: `B_k ≥ (5/4) A_k` and `C_k ≥ (5/4) D_k` for tensions ≥ 3/4, and `B = 2A`, `C = 2D` at tension 1.

### a.4 The velocity function and the control points

For a segment with angles `θ = θ_k`, `φ = φ_{k+1}` ([Hobby eq. (11)](https://link.springer.com/content/pdf/10.1007/BF02187690.pdf); [mf.web §116](https://raw.githubusercontent.com/TeX-Live/texlive-source/trunk/texk/web2c/mf.web)):

```
            2 + √2 (sin θ − sin φ / 16)(sin φ − sin θ / 16)(cos θ − cos φ)
f(θ, φ) = ───────────────────────────────────────────────────────────────
              1 + ½(√5 − 1) cos θ + ½(3 − √5) cos φ

r = f(θ, φ) / (3 τ_k)          s = f(φ, θ) / (3 τ̄_{k+1})        both reduced to 4 if larger

z_k⁺     = z_k     + r · e^{ iθ} · δ_k
z_{k+1}⁻ = z_{k+1} − s · e^{−iφ} · δ_k
```

- Hobby's general form is `ρ = (2 + α)/(1 + (1−c) cos θ + c cos φ)`, `σ = (2 − α)/(1 + (1−c) cos φ + c cos θ)`, `α = a (sin θ − b sin φ)(sin φ − b sin θ)(cos θ − cos φ)`. A least-squares fit suggested `a = 1.597, b = 0.0700, c = 0.370`; "METAFONT uses the slightly perturbed values `a = √2, b = 1/16, c = (3 − √5)/2`" ([paper, p. 133](https://link.springer.com/content/pdf/10.1007/BF02187690.pdf)).
- METAFONT's fixed-point constants are `379625062 ≈ 2^28·√2`, `497706707 ≈ 3·2^27·(√5 − 1)`, `307599661 ≈ 3·2^27·(3 − √5)` ([mf.web §116](https://raw.githubusercontent.com/TeX-Live/texlive-source/trunk/texk/web2c/mf.web)).
- Check values **[measured]**: `f(0,0)/3 = 1/3`; `f(45°,45°)/3 = 0.3905242918`; `f(22.5°,22.5°)/3 = 0.3465220433`; `f(30°,60°)/3 = 0.4234052732`; `f(60°,30°)/3 = 0.3673868237`; `f(90°,90°)/3 = 2/3`.
- For `θ = φ` the formula is `2/(1 + cos θ)` ([paper eq. (9)](https://link.springer.com/content/pdf/10.1007/BF02187690.pdf)), so the handle is `d · (2/3)/(1 + cos θ) = (4/3) tan(θ/2) · R` for a chord of a circle of radius R. That is the exact standard circle handle. **[inference, checked numerically]**

**`atleast`** (the `...` operator). If `sin θ` and `sin φ` have the same sign and `S = |sin θ| cos φ + |sin φ| cos θ > 0`, METAFONT multiplies S by the safety factor `1 + 2^-12` and then enforces `r ≤ |sin φ| / S` (when the outgoing tension is `atleast`) and `s ≤ |sin θ| / S` (when the incoming one is) ([mf.web §299-300](https://raw.githubusercontent.com/TeX-Live/texlive-source/trunk/texk/web2c/mf.web)). This keeps the control points inside the triangle of the two tangents and the chord. The directions are not recomputed.

### a.5 Properties that matter for a kernel

- **Mock curvature** is the first-order term of the true end curvature: `k̂(θ, φ, τ, τ̄) = τ² (2(θ + φ)/τ̄ − 6θ)`; the relative difference from the true curvature is below 0.11 when `|θ|, |φ| ≤ 22.5°` ([paper eq. (13) and p. 136](https://link.springer.com/content/pdf/10.1007/BF02187690.pdf)). **[measured]** true curvature jumps at free knots: 8.5-14.8 % on the MetaPost manual path below, 1.5-11.6 % on an irregular 5-knot cycle, 0 % on symmetric ovals.
- **Locality**: a change in one direction decays by at least a factor `3τ_min − 1` per knot, so at least 2 per knot at default tension; 4 per knot is typical ([paper, pp. 137-139](https://link.springer.com/content/pdf/10.1007/BF02187690.pdf)).
- **Invariance** holds under shift, rotation and uniform scaling, but "this invariance property does not hold if the points or paths are xscaled and yscaled by separate amounts" ([METAFONTbook ch. 14](https://mirrors.ctan.org/systems/knuth/dist/mf/mfbook.tex)). **[measured]** `(a,0){up}..{left}(0,b)` at tension 1: 250×250 gives k = 0.5523 on both handles; 250×270 gives 0.539 and 0.567 (0.11 % of radius off the ellipse); 250×300 gives 0.524 and 0.593 (0.41 %); 250×500 gives 0.479 and 0.823 (5.8 %).
- **Instability near a 180° turn**: `ψ` is reduced into `[−180°, 180°]`, so a turning angle near ±180° can flip sign. Jackowski shows `(0,0)..((100,0) rotated 15.03189)..cycle` reversing its orientation when the angle changes by 0.0003°, and five nearly collinear knots changing shape when one moves by `2^-16` ([TUGboat 34:2, §6.4](https://tug.org/TUGboat/tb34-2/tb107jackowski.pdf)).
- Levien's assessment: Hobby's spline is a cheap approximation of the Euler spiral spline, "≈ G2", with top marks for robustness, good "if … the input control points are closely enough spaced that angles are small"; it "converges to roundness as O(n^6)" ([thesis §4.7 and Table 4.1](https://levien.com/phd/thesis.pdf)).
- Tension 2 moves the control points halfway in; with given directions the handle lengths are simply divided by the tension ([METAFONTbook ch. 14](https://mirrors.ctan.org/systems/knuth/dist/mf/mfbook.tex)). **[measured]** for a symmetric 90° arc the handle ratio is `k = 0.5523/τ`: τ = 0.9 gives 0.614, 0.85 gives 0.650, 0.8 gives 0.690, the minimum 0.75 gives 0.736.

### a.6 Test vectors

All computed by `/tmp/claude-0/-home-user-experiments/a86123d7-7ed9-5f3d-9952-1d096afee651/scratchpad/research/hobby_check.py` (stdlib Python, two solvers that must agree to 1e-9: a dense Gaussian solve of the system above and METAFONT's u/v/w sweep).

**T1. Published: MetaPost manual §4.1.** `(0,0)..(60,40)..(40,90)..(10,70)..(30,50)`. The manual prints the result to one decimal ([mpman.pdf](https://mirrors.ctan.org/systems/doc/metapost/mpman.pdf)): controls (26.8,−1.8) and (51.4,14.6); (67.1,61.0) and (59.8,84.6); (25.4,94.0) and (10.5,84.5); (9.6,58.8) and (18.8,49.6). Computed:

```
ψ (deg):  78.111342, 101.888658, 101.309932 at knots 1..3
θ (deg):  −37.634400, −40.476942, −49.039693, −46.898219, +46.898219
(0,0)   .. controls (26.764622, −1.845435) and (51.409393, 14.584412) .. (60,40)
(60,40) .. controls (67.098752, 61.001887) and (59.762534, 84.575180) .. (40,90)
(40,90) .. controls (25.357136, 94.019469) and (10.480636, 84.502202) .. (10,70)
(10,70) .. controls ( 9.628946, 58.804210) and (18.804210, 49.628946) .. (30,50)
```

Largest difference from the printed values: 0.0454, inside the rounding of one decimal.

**T2.** `(0,0)..(100,100)..(200,0)` (curl 1 at both ends): `θ = 45°, 45°, −45°`.

```
(0,0)     .. controls (0, 55.228475) and (44.771525, 100) .. (100,100)
(100,100) .. controls (155.228475, 100) and (200, 55.228475) .. (200,0)
```

Radial deviation from the circle of radius 100 about (100,0): at most 0.0272 units (0.027 % of r).

**T3.** Cyclic unit circle `(1,0)..(0,1)..(−1,0)..(0,−1)..cycle`: every handle has length `0.5522847498 = (4/3)(√2 − 1)`; first segment `(1,0) .. controls (1, 0.5522847) and (0.5522847, 1) .. (0,1)`. Radial deviation 0 to +2.725e-4.

**T4. Published: The METAFONTbook ch. 14.** `(0,3)---(0,0)---(3,0)` "is equivalent to" controls (−0.0002,2.9998) and (−0.0002,0.0002), then (0.0002,−0.0002) and (2.9998,−0.0002); and `(0,3)--(0,0)` has controls (0,2) and (0,1) ([mfbook.tex](https://mirrors.ctan.org/systems/knuth/dist/mf/mfbook.tex)). Computed with tension 4095.99998: (−0.00020, 2.99980), (−0.00020, 0.00020), (0.00020, −0.00020), (2.99980, −0.00020); largest difference 0.000002.

**T5.** plain.mf's `quartercircle` before scaling, `(1,0){up}..(1,1)/√2..{left}(0,1)`: handle 0.265216490 = `(4/3) tan(π/16)`, radial deviation at most 4.2e-6.

**T6. Mixed case.** `(0,0){dir 60}..tension 1.2 and .9..(50,30)..(90,−10)..tension .75 and 2..{curl 2}(140,20)`:

```
θ (deg): 29.036243, 24.903009, −57.848015, 65.183210
(0,0)    .. controls (  9.613574,  16.651198) and ( 27.786298, 38.127738) .. (50,30)
(50,30)  .. controls ( 68.495322,  23.232775) and ( 72.685786, −1.221978) .. (90,−10)
(90,−10) .. controls (122.708978, −26.582913) and (141.346519,  7.497308) .. (140,20)
```

**How these were verified.** T1 and T4 are published values from primary sources and are reproduced. All of T1, T2, T3, T5, T6, a 5-knot cycle with tensions, and three `...` superellipse quadrants were also compared with [PyX](https://pyx-project.org/) 0.18's `pyx.metapost.path`, a Python port of MetaPost's `mp_make_choices`: largest difference 4e-10 (the `atleast` case), otherwise below 3e-14. The check runs with `python hobby_check.py --pyx`. METAFONT itself computes in fixed point (`scaled` is a multiple of 2^-16), so a real `mf`/`mpost` run will differ from these floats in about the fifth decimal.

---

## (b) penpos, penstroke, and how Computer Modern builds joins, terminals and slant

### b.1 The model

- `penpos k(b, d)` is two equations: `z_k = ½[z_kl, z_kr]` and `z_kr = z_kl + (b, 0) rotated d` ([METAFONTbook ch. 4](https://mirrors.ctan.org/systems/knuth/dist/mf/mfbook.tex); [plain.mf](https://mirrors.ctan.org/systems/knuth/dist/lib/plain.mf)). `b` is the breadth, `d` the angle of the pen's edge against the horizontal.
- `penstroke` with a path in `z_ke` fills `p.l -- reverse p.r -- cycle`, where `p.l` and `p.r` are the same path expression with `e` replaced by `l` and `r` ([plain.mf](https://mirrors.ctan.org/systems/knuth/dist/lib/plain.mf)). So the two edges are **two independent Hobby paths through the offset knots**; they are not offset curves of the centre line. Direction specifiers in the expression apply to both edges.
- The stroke ends are straight cuts along the pen line `z_kl -- z_kr` of the first and last position. **[inference from the macro]**
- A cyclic penstroke is `fill` of one edge and `unfill` of the other.
- Limitation stated by Knuth: "The left and right edges of a penpos-made pen must never cross, hence it is necessary to turn the pen when going around a curve" ([METAFONTbook ch. 4](https://mirrors.ctan.org/systems/knuth/dist/mf/mfbook.tex)).

### b.2 Computer Modern's version: `pos`, `stroke`, `filldraw`

- `pos k(b, d)` is `penpos` with breadth `b − currentbreadth`; `stroke` returns the closed outline `path_.l -- reverse path_.r -- cycle`; glyph programs say `filldraw stroke …`, which fills the outline and also draws it with a small circular nib ([cmbase.mf](https://mirrors.ctan.org/fonts/cm/mf/cmbase.mf)). The nib rounds the corners and restores the breadth.
- Nib diameters in cmr10: `tiny# = 8/36pt`, `fine# = 7/36pt`, `crisp# = 0` against `stem# = 25/36pt` ([cmr10.mf](https://mirrors.ctan.org/fonts/cm/mf/cmr10.mf)). In cmtt10: `tiny# = crisp# = 22/36pt`, `fine# = 21/36pt` against `stem# = hair# = curve# = 25/36pt`, `vair# = 22/36pt` ([cmtt10.mf](https://mirrors.ctan.org/fonts/cm/mf/cmtt10.mf)). The typewriter face is drawn almost entirely by a round nib nearly as wide as the stem. **[inference]** This is why cmtt has round terminals, and it is the part that does not carry over to outline fonts.

### b.3 Bowls: `super_arc` and `pulled_arc`

- The `o` has four pen positions at the extremes (`vair` at 90° and −90°, `curve` at 180° and 0°) and is one `penstroke` of four `pulled_arc.e` quadrants ([romanl.mf](https://mirrors.ctan.org/fonts/cm/mf/romanl.mf)).
- `super_arc` builds each edge of a quadrant from two `...` segments through the diagonal point `superness[center, corner]`, where the direction is parallel to the chord of the quadrant. `pulled_super_arc.l` moves the inner diagonal point `superpull` of the way towards the outer one ([cmbase.mf](https://mirrors.ctan.org/fonts/cm/mf/cmbase.mf)). The parameter comment calls `superpull` "extra openness inside bowls".
- `y2l := y4l := .52h` moves the inner side extremes off the outer ones in `o` ([romanl.mf](https://mirrors.ctan.org/fonts/cm/mf/romanl.mf)).

### b.4 The arch into the stem (`h_stroke`, used by h, m, n)

From [cmbase.mf](https://mirrors.ctan.org/fonts/cm/mf/cmbase.mf) and the `n` program in [romanl.mf](https://mirrors.ctan.org/fonts/cm/mf/romanl.mf):

1. The left stem is drawn thinner: `shaved_stem = hround(stem − 2 stem_corr)`.
2. Its lower part is thickened again up to `y = 1/8[bar_height, x_height]`.
3. The arch starts **inside** the stem at that height, with breadth `min(stem breadth, thin_join) − fine` and pen angle 180°. `thin_join#` is 7/36pt in cmr10 and 21/36pt in cmtt10.
4. It runs `z0e{up} ... {right}z1e` to the top position (`vair`, 90°, at `x_height + oo`), whose inner point is moved onto the line from the outer top to the inner start: `(x, y1l) = whatever[z1r, z0l]; x1l := x`.
5. From the top it is `super_arc.e` down into the right stem, with `superness` raised to `hein_super`.

So the join is made by overlap of two closed strokes, with an explicit thin-join breadth, not by a boolean-free single outline.

### b.5 Terminals

- Sans terminals use `term.l/r($, $$, d, t, s)`: `z${d}..tension t..z$$`, replaced by a `tension atleast t` curve with an explicit end direction when the first form ends too steeply; the comment calls it a "robust" sans-serif terminal ([cmbase.mf](https://mirrors.ctan.org/fonts/cm/mf/cmbase.mf)).
- In the sans `c`, the upper terminal is `pos1(4/7[vair', flare], 80)` with `term.e(2, 1, right, .8, 4)`: the cut is the pen line at 80°. The lower terminal uses tension `.9 and 1` and caps the end direction at 75° ([romanl.mf](https://mirrors.ctan.org/fonts/cm/mf/romanl.mf)). Levien notes 0.9 is the most common non-default tension in Computer Modern ([thesis §4.7](https://levien.com/phd/thesis.pdf)).

### b.6 Slant

- `font_setup` sets `currenttransform := identity slanted slant yscaled aspect_ratio scaled granularity`, and `fill`/`draw` apply it to every path ([cmbase.mf](https://mirrors.ctan.org/fonts/cm/mf/cmbase.mf); [plain.mf](https://mirrors.ctan.org/systems/knuth/dist/lib/plain.mf)). Glyphs are computed upright; the finished paths are sheared. A shear maps a cubic to the cubic of its sheared control points, so nothing is lost. **[inference]**
- `slant` values: 0 in cmr10 and cmtt10, 1/6 in cmsl10 and cmsltt10, 0.25 in cmti10 and cmitt10, `sind 12/cosd 12` in cmssi10 ([cm/mf](https://mirrors.ctan.org/fonts/cm/mf/)).
- **[measured]** The order matters because Hobby's rule is not shear-invariant. For a 450×500 oval with directions at the four extremes, solving upright then shearing and shearing the knots and directions then solving differ by 3.9 units at slant 1/6, 4.7 at 0.2 and 6.1 at 0.25. After shearing, the x-extrema sit inside the two side segments at `t = 0.116`, `0.139`, `0.172` for those slants.

---

## (c) A superellipse quadrant as one cubic

### c.1 The formula

Quadrant of `|x/a|^n + |y/b|^n = 1` from `(a, 0)` to `(0, b)` as the cubic `(a,0), (a, k·b), (k·a, b), (0,b)`.

- The curve point at `t = ½` is `((4 + 3k)/8)·(a, b)`. The superellipse crosses the diagonal at `σ·(a, b)` with `σ = 2^(−1/n)`. Passing through it requires

  **`k(n) = (8·2^(−1/n) − 4)/3`**, and conversely `σ = (4 + 3k)/8`, `n = ln 2 / ln(1/σ)`. **[derivation, checked numerically]**

- `σ` is exactly METAFONT's `superness`: "corner points (±σa, ±σb), where σ = 2^(−1/β) is the superness. The tangent to the curve at (σa, σb) runs in the direction (−a, b)" ([METAFONTbook ch. 14](https://mirrors.ctan.org/systems/knuth/dist/mf/mfbook.tex)). The cubic above has that tangent at `t = ½` by symmetry.
- `n = 2` gives `k = (4/3)(√2 − 1) = 0.5522847`, the circle value.
- A single cubic of this form needs `k ≤ 1` to avoid a cusp, so it can reach at most `σ = 7/8`, `n = 5.19`. **[inference]**

### c.2 Accuracy **[measured]**

Radial error is `(x^n + y^n)^(1/n) − 1` along the cubic, in percent of the radius.

| n | superness σ | k through the 45° point | radial error | minimax k | its max error |
|---|---|---|---|---|---|
| 2.000 | 0.707107 | 0.552285 | 0 … +0.027 % | 0.551915 | 0.020 % |
| 2.100 | 0.718873 | 0.583662 | −0.086 … 0 % | 0.584948 | 0.067 % |
| 2.200 | 0.729740 | 0.612640 | −0.184 … 0 % | 0.615406 | 0.142 % |
| 2.275 | 0.737359 | 0.632958 | −0.249 … 0 % | 0.636732 | 0.192 % |
| 2.400 | 0.749154 | 0.664409 | −0.343 … 0 % | 0.669674 | 0.264 % |
| 2.500 | 0.757858 | 0.687622 | −0.406 … 0 % | 0.693915 | 0.311 % |
| 3.000 | 0.793701 | 0.783201 | −0.595 … 0 % | 0.792771 | 0.452 % |
| 4.000 | 0.840896 | 0.909057 | −0.612 … 0 % | 0.919208 | 0.453 % |
| 5.000 | 0.870551 | 0.988135 | −0.440 … 0 % | 0.995375 | 0.312 % |

For a 250-unit radius, the 45°-point fit is within 0.62 units of the true superellipse for `n ≤ 2.275` and within 1.0 unit for `n ≤ 2.5`. plain.mf's own `superellipse` (two `...` segments per quadrant) is no closer: 0.24 % at σ = 8/11, 0.35 % at σ = 0.75 and 2^-0.4, 0.77 % at σ = 2^-0.25. Knuth says as much: the routine "does not produce a perfect superellipse" ([METAFONTbook ch. 14](https://mirrors.ctan.org/systems/knuth/dist/mf/mfbook.tex)).

The circle constant: `k = 0.5522847` errs 0 … +0.0273 % of r; `k = 0.5519150` errs ±0.0196 %; `k = 0.551784` errs −0.0266 … +0.0173 %; the round "55 %" errs −0.121 … +0.001 %. **[measured]**

### c.3 Values in use

| source | value | as σ | as k | as n |
|---|---|---|---|---|
| Circle | — | 0.7071 | 0.5523 | 2 |
| cmr10, cmtt10, cmss10, cmti10 `superness` ([cm/mf](https://mirrors.ctan.org/fonts/cm/mf/)) | 1/√2 | 0.7071 | 0.5523 | 2 |
| cmbx10 `superness` | 8/11 | 0.7273 | 0.606 | 2.18 |
| cminch `superness` | 3/4 | 0.7500 | 0.667 | 2.41 |
| cmff10 `superness` | 2/3 | 0.6667 | 0.444 | 1.71 |
| CM `more_super = max(superness, sqrt(.77 superness))` at 1/√2 ([cmbase.mf](https://mirrors.ctan.org/fonts/cm/mf/cmbase.mf)) | — | 0.7379 | 0.634 | 2.28 |
| CM `hein_super`, used for the n/h/m arch | sqrt(2^-0.3 · superness) | 0.7579 | 0.688 | 2.5 |
| Piet Hein ([METAFONTbook](https://mirrors.ctan.org/systems/knuth/dist/mf/mfbook.tex)) | β = 2.5 | 0.7579 | 0.688 | 2.5 |
| METAFONTbook: "values in the vicinity of 0.75 are usually preferred"; allowed 0.5 (diamond) to 1.0 (square) | — | 0.75 | 0.667 | 2.41 |
| METAFONTbook typewriter `0` / ambiguous / `O` | 2^-0.5 / 0.77 / 2^-0.25 | 0.707 / 0.77 / 0.841 | 0.552 / 0.720 / 0.909 | 2 / 2.65 / 4 |
| Iosevka `superness` ([aesthetics.ptl](https://raw.githubusercontent.com/be5invis/Iosevka/main/packages/font-glyphs/src/meta/aesthetics.ptl)) | n = 2.275 (tight hooks 2.30) | 0.7374 | 0.633 | 2.275 |
| Glyphs: circle ([harmonization tutorial](https://glyphsapp.com/learn/harmonization)) | 55 % | — | 0.55 | — |
| Glyphs: "almost all handle lengths (on 90° curve segments) end up between approximately 58% and 76%" | 58-76 % | 0.7175-0.785 | 0.58-0.76 | 2.09-2.86 |
| Glyphs: very bold weights | 64-78 % | 0.74-0.7925 | 0.64-0.78 | 2.31-2.98 |

What the tools call it:

- Glyphs measures a handle as a percentage of the distance from its node to the point where the two handles' lines intersect: "100% means the two handles meet in their intersection point"; "an ellipse or circle usually clocks in at … approximately 55-56%"; average handle lengths "stay well below 80%" ([drawing good paths](https://glyphsapp.com/learn/drawing-good-paths); [harmonization](https://glyphsapp.com/learn/harmonization)). For a 90° axis-aligned segment this percentage is exactly `k`. Glyphs calls the operation "Fit Curve" and the quantity "relative handle length", "sometimes (imprecisely) referred to as the curvature".
- Glyphs on inside and outside: "the smaller inside curve needs higher relative handle lengths; the corresponding larger outside curve needs smaller relative handle lengths"; one Fit Curve step of difference in normal weights, two or three in very bold ones ([harmonization](https://glyphsapp.com/learn/harmonization)).
- Balanced handles are called "Tunnification" after Eduardo Tunni ([drawing good paths](https://glyphsapp.com/learn/drawing-good-paths)). Curve Equalizer offers "Circle", "Rule of thirds", "Balance", "Fixed", "Adjust" and a "Hobby" mode that changes the tension ([Curve Equalizer](https://jenskutilek.github.io/Curve-Equalizer)).
- I found no primary RMX Tools documentation that defines a "curve tension" value; the Glyphs tutorial only says the RMX Harmonizer "manages to smoothen the transitions to G2" and that G3 is what type designers call "supersmooth".

---

## (d) Offset curves by one cubic, and a method for per-knot widths

### d.1 What the literature says

- The offset `C_d(t) = C(t) + d·N(t)` of a polynomial curve is not polynomial or rational in general ([Elber, Lee and Kim](https://gershon.cs.technion.ac.il/papers/offset-compare.pdf)); for a cubic it is "an analytic curve of degree 10" ([Levien 2022](https://raphlinus.github.io/curves/2022/09/09/parallel-beziers.html)).
- The end derivative is exact: `C_d'(t) = (1 + d κ(t)) C'(t)` in Elber's normal orientation. A cusp appears where `1 + d κ = 0` ([Elber et al.](https://gershon.cs.technion.ac.il/papers/offset-compare.pdf); [Levien 2022](https://raphlinus.github.io/curves/2022/09/09/parallel-beziers.html)).
- **Tiller and Hanson (1984)** translate each edge of the control polygon by `d` along the edge normal. Elber et al.: it "outperforms all the other methods for the case of offsetting (piecewise) quadratic curves", but for higher degree "has a similar performance to that of Cobb". For their cubic Bézier example it needs 73 control points at tolerance 1e-3 and 715 at 1e-5, against 31 and 106 for Hoschek's local least squares ([Elber et al., Fig. 7](https://gershon.cs.technion.ac.il/papers/offset-compare.pdf)). Levien: Tiller-Hanson scales as O(n²), "only a constant factor better than subdividing the curves into lines" ([Levien 2022](https://raphlinus.github.io/curves/2022/09/09/parallel-beziers.html)). I did not read the 1984 paper itself.
- **Klass (1983)**: a cubic Hermite curve through the exact end points and end velocities; "quite unstable when the offset curve becomes almost flat". **Hoschek (1988)**: keep the end directions parallel to `C'` and choose the two handle lengths by least squares; "the least squares methods … perform much better than all the other methods, especially when high precision is required" for cubics ([Elber et al.](https://gershon.cs.technion.ac.il/papers/offset-compare.pdf)).
- **Levien (2022)**: fix end points and end tangents, then choose the two handle lengths so that signed area and x-moment match the true offset; this is a quartic. He claims O(n^6) scaling against O(n^5) for Yang-Huang "shape control" and O(n^4) for his Euler-spiral method, and notes the fit "can be adapted to generalized strokes, for example where the stroke width is variable" ([Levien 2022](https://raphlinus.github.io/curves/2022/09/09/parallel-beziers.html)).
- A warning from the same author: for C-shaped curves "there tend to be three sets of parameters that produce extremely similar shapes", so a two-handle fit has three local minima ([Levien 2021](https://raphlinus.github.io/curves/2021/03/11/bezier-fitting.html)).
- **Kinch's MetaFog** fitted each side of a pen envelope with end points, end tangent angles and the midpoint as constraints: "quite good when curves are not too 'sharp' … do not turn through more than 90 degrees, and are not too 'tight'"; otherwise bisect ([TUGboat 16:3](https://tug.org/TUGboat/tb16-3/tb48kinc.pdf)).

### d.2 Accuracy of one cubic with matched end tangents **[measured]**

Maximum distance, in units, between the true offset (sampled at 2001 points) and one cubic. Methods: Tiller-Hanson; "end-speed" (handles multiplied by the exact factor `1 − dκ` at each end, Klass-like); "midpoint" (handle lengths from the 2×2 linear system that makes the cubic pass through the true offset point of `t = ½`, Kinch-like); two-handle least squares (Hoschek-like).

| source cubic | d | Tiller-Hanson | end-speed | midpoint | least squares |
|---|---|---|---|---|---|
| quarter circle r = 250 | ±35 | 2.56 | 0.22 | 0.010 | 0.007 |
| quarter circle r = 250 | ±60 | 4.39 | 0.38 | 0.016 | 0.012 |
| bowl 250×270, k = 0.64 | +35 (inside) | 2.57 | 3.27 | 0.127 | 0.048 |
| bowl 250×270, k = 0.64 | −35 (outside) | 2.57 | 3.27 | 0.116 | 0.035 |
| bowl 250×270, k = 0.64 | +60 | 4.41 | 5.62 | 0.228 | 0.181 |
| bowl 250×270, k = 0.64 | −60 | 4.40 | 5.61 | 0.193 | 0.055 |
| shoulder of n | ±35 | 1.90 | 1.16 | 0.029 | 0.004 |
| shoulder of n | ±60 | 3.26 | 1.99 | 0.052 | 0.009 |
| S spine with inflection | ±35 | 15.3 | 4.20 | singular | 2.02 |
| S spine with inflection | ±60 | 27.1 | 8.28 | singular | 3.16 |
| tight hook r = 90, k = 0.60 | +35 | 2.56 | 2.00 | 0.022 | 0.016 |
| tight hook r = 90, k = 0.60 | +60 (`1 − dκ` down to 0.23) | 4.39 | 3.43 | 0.080 | 0.058 |

- Splitting the source at `t = ½` divides the error by 3.4-3.9 for Tiller-Hanson (O(n²), as Levien says), by 3.6-11 for the midpoint method, by 10-47 for least squares.
- The midpoint method stays under 0.25 units for every convex segment of at most 90° tried, up to half-width 60. Its system is singular when the end tangents are parallel, so an S segment must be split at its inflection first; after the split the S spine fits to 0.18 (d = 35) and 0.44 (d = 60), and least squares to 0.08 and 0.30.
- **The midpoint fit is exactly linear in `d`**: end points, the target midpoint and the right-hand side are linear in `d`, and the tangent directions do not change. Rails fitted at half-width 20 and 60 and interpolated linearly at 40 equal the rails fitted at 40 to 0.000 units. **[measured, and it follows from the algebra]**
- Squareness of true offsets: the offsets of a centre line with `k = 0.64` are best fitted with balanced handles by `k = 0.653` inside and `0.630` outside at half-width 35 (error under 0.09), and `0.665` and `0.624` at half-width 60. Keeping `k = 0.64` on both edges instead is off by 1.6 units at 35 and 2.8 at 60. This is the Glyphs rule of thumb in numbers.
- Unconstrained two-handle least squares returned unbalanced handles (0.576 and 0.726 for the inside curve) for almost the same shape, which is Levien's three-minima effect.

### d.3 A simple robust method for per-knot widths

The true variable-width edge is `r(t) = c(t) ± w(t) n(t)`, with `r' = c'(1 ∓ wκ) ± w' n`. **[derivation]** Its tangent is parallel to the skeleton's only where `w' = 0`.

**[measured]** on the 250×270 bowl, one cubic per edge, end tangents kept parallel to the skeleton:

| half-width | law for `w(t)` | true tangent rotation at the ends | midpoint fit error | least-squares error |
|---|---|---|---|---|
| 35 → 30 | smoothstep `3t² − 2t³` | 0° | 0.13-0.17 | 0.04 |
| 35 → 30 | linear in t | 0.5-0.65° | 0.61-0.64 | 0.29-0.42 |
| 35 → 22 | smoothstep | 0° | 0.41-0.49 | 0.08-0.18 |
| 35 → 22 | linear in t | 1.3-1.6° | 1.6-1.7 | 1.2-1.4 |
| 60 → 40 | smoothstep | 0° | 0.55-0.78 | 0.16-0.29 |
| 60 → 40 | linear in t | 2.0-2.7° | 2.5-2.6 | 1.9-2.0 |

The method this supports:

1. Solve the skeleton as cubics, with a direction at every knot.
2. Give each knot a half-width (left and right may differ) and, optionally, a pen angle. Edge knots are `z_k ± w_k n_k`; with a pen angle the normal is replaced by the pen direction, as in `penpos`.
3. Blend the width inside a segment with a law that is flat at both knots (smoothstep). Then both edges are tangent to the skeleton direction at every knot, G1 holds on the edges whenever it holds on the skeleton, and extremes of the skeleton are extremes of both edges.
4. Fit each edge segment with the midpoint system: 2 unknown handle lengths, 2 linear equations. Split at inflections first.
5. Check 16 interior samples against `c(t) ± w(t) n(t)`; accept under a fixed tolerance; otherwise the glyph program must add a knot. Reject a segment where `1 ∓ wκ` falls below about 0.2 on the inside edge.

Iosevka and METAFONT both do step 2 and then **re-interpolate** each edge as its own spline (spiro and Hobby respectively) rather than fit the offset; see (b.1) and (f.1).

---

## (e) Rules for clean outlines, and cubic-to-quadratic conversion

### e.1 Rules, with their sources

| rule | source |
|---|---|
| A node at "most horizontal or vertical extremes"; "most curves should not include more than 90 degrees of arc"; not needed on very small curves such as serif tips | [Adobe Type 1 Font Format §4.1](https://adobe-type-tools.github.io/font-tech-notes/pdfs/T1_SPEC.pdf) |
| "No extremums, no stem hint"; but avoid an extremum that creates a curve "only a handful of units deep" | [Glyphs: drawing good paths](https://glyphsapp.com/learn/drawing-good-paths) |
| At a smooth join the node and its neighbouring control points "should all be collinear … especially important at horizontal and vertical extremes" | [Type 1 §4.2](https://adobe-type-tools.github.io/font-tech-notes/pdfs/T1_SPEC.pdf) |
| Fewest segments; no consecutive collinear lines; no lines drawn as curves; close with `closepath`, no zero-length closing segment | [Type 1 §4.3](https://adobe-type-tools.github.io/font-tech-notes/pdfs/T1_SPEC.pdf) |
| Equal stems exactly equal; aligned features at exactly the same y | [Type 1 §4.4](https://adobe-type-tools.github.io/font-tech-notes/pdfs/T1_SPEC.pdf) |
| Filled subpaths counterclockwise, unfilled clockwise; a closed outline must not intersect itself; avoid overlapping subpaths | [Type 1 §3.5-3.6](https://adobe-type-tools.github.io/font-tech-notes/pdfs/T1_SPEC.pdf) |
| Handles stay inside the triangle of the two nodes and the intersection of the handle lines; no handle crosses the other; beyond 100 % "the curve segment will inflect … causing cusps and false extremums" | [Glyphs: drawing good paths](https://glyphsapp.com/learn/drawing-good-paths), [harmonization](https://glyphsapp.com/learn/harmonization) |
| No "zero handle or half-dead curve" (a control point hidden in its node) | [Glyphs: drawing good paths](https://glyphsapp.com/learn/drawing-good-paths) |
| Avoid inflections inside a segment where the design allows; an inflection node "can cause a so-called 'kink' in interpolated steps between masters" | [Glyphs: drawing good paths](https://glyphsapp.com/learn/drawing-good-paths) |
| Balanced handles; different handle distributions between masters give a "hang-through" in between | [Glyphs: drawing good paths](https://glyphsapp.com/learn/drawing-good-paths) |
| G2 between curves is the target; "approximate G2 continuity will suffice just nicely" | [Glyphs: harmonization](https://glyphsapp.com/learn/harmonization) |
| Lint thresholds: on-curve point within 2 units of a metric line but not on it; segment shorter than 3 units or 0.6 % of its contour; consecutive lines within 0.1 rad; corner sharper than 0.25 rad; line within 0.5° of horizontal or vertical | [fontbakery outline checks v0.12](https://raw.githubusercontent.com/fonttools/fontbakery/v0.12.0/Lib/fontbakery/checks/outline.py) |

**Rounding and G1 [measured].** Rounding a smooth node and both of its control points to integers leaves a kink. For random directions and both handles of length L, the largest kink is 16.3° at L = 5, 8.1° at 10, 4.1° at 20, 2.05° at 40, 1.02° at 80 and 0.51° at 160 (median about a third of that). At a horizontal or vertical extremum the kink is exactly 0, because the three points share a coordinate before and after rounding.

### e.2 cu2qu

From [fontTools/cu2qu/cu2qu.py](https://raw.githubusercontent.com/fonttools/fonttools/main/Lib/fontTools/cu2qu/cu2qu.py) and [cu2qu/ufo.py](https://raw.githubusercontent.com/fonttools/fonttools/main/Lib/fontTools/cu2qu/ufo.py):

- **Default tolerance**: `DEFAULT_MAX_ERR = 0.001`, in em. `fonts_to_quadratic` multiplies it by each font's `unitsPerEm`; `glyphs_to_quadratic` uses `0.001 * 1000 = 1` unit. ufo2ft documents the same default: "relative to the UPM of the font (default: 1/1000 or 0.001)" ([ufo2ft preProcessor](https://raw.githubusercontent.com/googlefonts/ufo2ft/main/Lib/ufo2ft/preProcessor.py)); fontmake exposes it as `-e/--conversion-error`, "measured in EM" ([fontmake](https://raw.githubusercontent.com/googlefonts/fontmake/main/Lib/fontmake/__main__.py)).
- **Algorithm**: try `n = 1 … MAX_N = 100` quadratic segments. For `n = 1` the control point is the intersection of the two end tangents. For `n ≥ 2` the cubic is cut into n equal parameter intervals; the off-curve point of piece i is a blend, by `t = i/(n−1)`, of `p0 + 1.5(p1 − p0)` and `p3 + 1.5(p2 − p3)`; the on-curve points between pieces are the implied midpoints of consecutive off-curve points. The result is a TrueType spline of `n + 2` points.
- **Error test**: each quadratic is degree-elevated (`q0 + (2/3)(q1 − q0)`), and the cubic that is the difference from the source piece must stay within the tolerance of the origin: the end deltas are tested directly and the interior by recursive halving (`cubic_farthest_fit_inside`). It bounds `max_t |Q(t) − C(t)|` at equal parameter, which is at least the geometric distance. There is no closed-form bound in the source.
- **Compatibility**: `curves_to_quadratic` takes the same curve from every master and raises `n` until all of them fit, so all masters get the same point count. `fonts_to_quadratic` "raises IncompatibleFontsError if same-named glyphs from different fonts have non-interpolatable outlines".
- For reference, the classical single-quadratic bound **[my derivation, not in the source]**: the quadratic with control point `(3P1 + 3P2 − P0 − P3)/4` differs from the cubic by `(Δ/2)·t(1−t)(2t−1)` with `Δ = P3 − 3P2 + 3P1 − P0`, so the maximum is `(√3/36)|Δ|`, and n equal pieces with explicit on-curve points give `(√3/36)|Δ|/n³`. cu2qu's implied-midpoint spline needs more segments than this but fewer stored points.

**[measured]** segments chosen and true geometric error:

| cubic | tol 1.0 (default at 1000 upm) | tol 0.5 | tol 0.25 |
|---|---|---|---|
| quarter circle r = 250 | n = 3, 0.38 | n = 4, 0.21 | n = 5, 0.12 |
| bowl 250×270, k = 0.64 | n = 2, 0.21 | n = 3, 0.11 | n = 3, 0.11 |
| shoulder of n | n = 2, 0.48 | n = 3, 0.23 | n = 4, 0.11 |
| S spine with inflection | n = 6, 0.69 | n = 7, 0.43 | n = 9, 0.20 |
| tight hook r = 90 | n = 2, 0.16 | n = 2, 0.16 | n = 3, 0.09 |

### e.3 Format facts that constrain the kernel

- ufo2ft assumes sources follow "the PostScript counter-clockwise convention" and reverses contours for TrueType unless told not to ([ufo2ft preProcessor](https://raw.githubusercontent.com/googlefonts/ufo2ft/main/Lib/ufo2ft/preProcessor.py)).
- Variable fonts: "corresponding glyph outlines must be point-compatible: they must have the same number of contours and the same number of points in each contour" ([OpenType variations overview](https://learn.microsoft.com/en-us/typography/opentype/spec/otvaroverview)).
- The same page asks implementations to keep at least 16 fractional bits and to round "only when the final result is used".
- `glyf` coordinates are integers in font design units; `OVERLAP_SIMPLE` (0x40): "Variable fonts often make use of overlapping contours"; a tool that derives a static instance "should either set the OVERLAP_SIMPLE flag … or else should merge contours" ([glyf](https://learn.microsoft.com/en-us/typography/opentype/spec/glyf)).

---

## (f) Lessons and pitfalls reported by programmatic font projects

### f.1 Iosevka (source read at version 34.9.1)

- **Model**: each knot carries left and right half-widths `d1`, `d2`, an optional `proposedNormal` (`heading`) and an `unimportant` flag ([spiro-expand.mjs](https://raw.githubusercontent.com/be5invis/Iosevka/main/packages/geometry/src/spiro-expand.mjs); [spiro-kit.mjs](https://raw.githubusercontent.com/be5invis/Iosevka/main/packages/font-kits/src/spiro-kit.mjs)).
- **Expansion**: solve the centre spiro spline, read the tangent at every knot, place `lhs = z + d1·N`, `rhs = z − d2·N`, where the x component of `N` is multiplied by `contrast`. Then take the midpoints of the expanded pairs as a new centre line and repeat, up to 8 times or until the mean squared tangent change is below 1e-8. Finally each side is solved **as its own spiro spline**; an open stroke becomes one closed contour with corner knots at the ends ([spiro-expand.mjs](https://raw.githubusercontent.com/be5invis/Iosevka/main/packages/geometry/src/spiro-expand.mjs); [index.mjs](https://raw.githubusercontent.com/be5invis/Iosevka/main/packages/geometry/src/index.mjs)).
- **Unimportant knots** are not offset: their side points are linear regressions between the neighbouring important knots, and spiro arcs are merged across them before conversion to cubics ([spiro-to-outline.mjs](https://raw.githubusercontent.com/be5invis/Iosevka/main/packages/geometry/src/spiro-to-outline.mjs)).
- **Arcs**: `archv`/`arcvh` insert 6 unimportant G2 knots on `x = cos^(2/s) θ`, `y = sin^(2/s) θ`, with `s = Superness = 2.275` ([spiro-kit.mjs](https://raw.githubusercontent.com/be5invis/Iosevka/main/packages/font-kits/src/spiro-kit.mjs); [aesthetics.ptl](https://raw.githubusercontent.com/be5invis/Iosevka/main/packages/font-glyphs/src/meta/aesthetics.ptl)).
- **Slant**: tangents and widths are computed on the transformed (slanted) knots, the side knots are transformed back, the side splines are solved upright, and the cubics are sheared at the end. The horizontal-to-vertical contrast is corrected for slope: `HVContrast = Contrast·cos(slope) + sin(slope)·tan(slope)` ([aesthetics.ptl](https://raw.githubusercontent.com/be5invis/Iosevka/main/packages/font-glyphs/src/meta/aesthetics.ptl)).
- **Parameters**: weight 400 has `stroke = 70`, `contrast = 1.11`; weight 100 has contrast 1.08, weight 900 has 1.20; `overshoot = −8` ([shape-weight.toml](https://raw.githubusercontent.com/be5invis/Iosevka/main/params/shape-weight.toml); [parameters.toml](https://raw.githubusercontent.com/be5invis/Iosevka/main/params/parameters.toml)).
- **Overlap removal**: `TypoGeom.Boolean.removeOverlap` with the non-zero rule at `BOOLE_RESOLUTION = 0x4000`, and it is done after transforming back to upright space, then transformed forward again. Tolerances: `OCCURRENT_PRECISION = 1/16` for spiro-to-cubic, `GEOMETRY_PRECISION = 1/4` for the final conversion to quadratics after a "fairize" pass ([curve-util.mjs](https://raw.githubusercontent.com/be5invis/Iosevka/main/packages/geometry/src/curve-util.mjs); [index.mjs](https://raw.githubusercontent.com/be5invis/Iosevka/main/packages/geometry/src/index.mjs)).
- The parameter file opens with a warning that changing the numbers "may make the builder crash / hang / produce broken shapes" ([parameters.toml](https://raw.githubusercontent.com/be5invis/Iosevka/main/params/parameters.toml)). I did not read the issue tracker.

### f.2 MetaType1 (Latin Modern's engine)

- "Pens are not allowed in MetaType1 programs. A user is responsible for constructing a proper outline of a glyph: paths should not cross each other … and should be properly oriented". Stroke expansion and overlap removal exist as macros, "but, in general, such operations cannot be reliably programmed in METAFONT/METAPOST" ([MAPS 26](https://www.ntg.nl/maps/26/15.pdf)).
- `find_outlines` "behaves unstably if the curves to be processed are tangent or nearly tangent … it is impossible to distinguish numerically between tangent curves and intersecting ones". `turningnumber` is unreliable because of "tiny loops" ([TUGboat 24:3](https://tug.org/TUGboat/tb24-3/jackowski.pdf)).
- Rounding: Type 1 "accepts only integer numbers, therefore rounding is necessary (a user should control the process of rounding at crucial points in METAPOST programs)" ([MAPS 26](https://www.ntg.nl/maps/26/15.pdf)).
- Auditing pays: converting CM-Super to MetaType1 source found "strange tiny paths" in about 25 % of the fonts, and the AMS cmsy10 had hints that did not match equal stems ([TUGboat 24:3](https://tug.org/TUGboat/tb24-3/jackowski.pdf)).
- "It is the parameterization of a font that is really a tough problem. We do not want to juggle lots of incoherent parameters … the Computer Modern fonts are governed by more than 60 parameters" ([TUGboat 24:3](https://tug.org/TUGboat/tb24-3/jackowski.pdf)).

### f.3 MetaFog (Kinch 1995)

- The two hard problems are "(1) finding the envelope of an elliptical pen stroked along a Bézier curve (an algebraic problem), and (2) reducing overlapping paths to an equivalent, non-overlapping contour (a topological problem)".
- The second was never fully automatic: "METAFONT output often has degenerate shapes and intersections that defy an automatic solution", so a human "weeder" picked the segments.
- "Exact" meant within one unit of a 1024 or 2048 unit em.
- METAFONT curves "tend to have control points every 45 degrees or so", while Type 1 rules "tend to add redundant control points" at extrema ([TUGboat 16:3](https://tug.org/TUGboat/tb16-3/tb48kinc.pdf)).

### f.4 mf2pt1

- "Each glyph must be drawn entirely from closed paths, using METAFONT's fill and unfill"; `draw` is discouraged.
- Overlaps are left to FontForge; the default script is `RemoveOverlap(); AddExtrema(); Simplify(0, 2); CorrectDirection(); Simplify(0, 2); RoundToInt(); AutoHint()`. The third option offered is "Design your fonts from the beginning without using overlapping paths".
- Coordinates are rounded to integers unless `--rounding` gives a finer step; MetaPost's fixed point overflows at 4096 ([mf2pt1.pdf](https://mirrors.ctan.org/support/mf2pt1/mf2pt1.pdf)).

### f.5 Metapolator

- It interpolates skeleton points and parameters as a linear combination of masters and then rebuilds the outline: "All points of all skeletons are calculated by this formula … All parameters are also calculated by the formula" ([wiki: metapolation](https://github.com/metapolator/metapolator/wiki/metapolation)).
- It "will work best when glyphs are drawn as separate, overlapping shapes with pairs of points along each edge"; the outline is "reconstructed from an inferred central skeleton (ductus) and Hobby splines" ([README](https://raw.githubusercontent.com/metapolator/metapolator/master/README.md)). I found no retrospective by the project.

### f.6 The build chain

- ufo2ft: for interpolatable output "overlaps are *not* removed as that could make outlines incompatible for interpolation", and custom filters may break compatibility ([ufo2ft preProcessor](https://raw.githubusercontent.com/googlefonts/ufo2ft/main/Lib/ufo2ft/preProcessor.py)).
- fontmake removes overlaps for static output unless `--keep-overlaps`; the backend is `booleanOperations` by default or `pathops` ([fontmake](https://raw.githubusercontent.com/googlefonts/fontmake/main/Lib/fontmake/__main__.py)).

---

## What this means for our font

Decisions, each with the evidence it rests on. Values are for 1000 units per em.

**1. Path solver.** Implement section (a) exactly, in double precision, with both solvers kept as a cross-check, and use T1-T6 as unit tests (tolerance 1e-6; T1 and T4 against the published decimals). Keep tension, curl and `atleast`.

**2. Give a direction at every knot that is an extreme, a stroke end or a join.** Then every segment is the two-direction case of a.4 and nothing propagates. Free knots are allowed only between such knots. Refuse a path whose chords turn by more than about 170° at a free knot (Jackowski's instability).

**3. Bowls and arches use an explicit handle ratio, not Hobby's velocity.** For a segment whose end tangents are perpendicular, set both handles to `k` times the distance to the tangent intersection, `k = (8σ − 4)/3`. It is affine-invariant, where Hobby's rule drifts 0.4 % of the radius at a 1:1.2 box. Start values **[inference from c.3]**: skeleton `k = 0.63` (σ = 0.736, n = 2.27, the value both Computer Modern's `more_super` and Iosevka use), `k = 0.69` for the n/h/m arch (Computer Modern's `hein_super`), allowed range 0.55-0.80, hard error at `k ≥ 1`. Use Hobby's velocity for segments with other angles.

**4. Stroke expansion by the midpoint fit, with flat-ended width blending.** Section d.3. Expected error: under 0.25 units per 90° segment at half-width up to 60, under 0.8 with a 60 → 40 width change. Set the build tolerance at 0.5 units and make a failure an error in the glyph program, not an automatic subdivision. Split S segments at the inflection in the skeleton. Put squareness on the skeleton only: the fit then gives the inside edge the higher ratio (0.653 against 0.630 at stem 70) without a second parameter.

**5. The weight axis.** With a fixed skeleton the fitted edges are exactly linear in the half-width, so two weight masters reproduce every intermediate weight exactly. Where the skeleton itself moves with weight (apertures, counters), compare the variable-font instance at the middle weight with the program run at that weight and add a master if they differ by more than 1 unit. **[inference; the second half needs the measurement]**

**6. Structure is decided by the program, never by a tolerance.** Number of knots, splits at inflections and inserted extrema must be the same in every master; the Python kernel should emit a structure signature per glyph and the build should compare it across masters before fontmake does.

**7. Slant.** Compute upright, shear the final control points (Computer Modern's way), then insert x-extrema by splitting the side segments; the split parameter is about 0.12-0.17 for slants 1/6-1/4 and the point count is the same in every italic master. Shearing keeps the horizontal thickness of vertical stems, which is the quantity the pixel grid sees; whether diagonal and curved strokes then need Iosevka's contrast correction is a design question to settle by measuring stroke thickness in the sheared outlines. Do not solve Hobby paths on sheared knots: it changes the shape by 4-6 units on an oval.

**8. Joins and terminals.** Build each stroke as its own closed contour and let strokes overlap, as Computer Modern's `h_stroke` and Iosevka do. Keep overlaps in the variable masters; let fontmake remove them for static fonts. Make every overlap deep: MetaType1 and MetaFog both report that tangent or nearly tangent contours are where union fails, so an arch should enter the stem by a clear margin and no two edges should coincide. A stroke end is the straight pen line of the last position; its angle is a parameter.

**9. Extremes, rounding, smoothness.**
- A knot at every horizontal and vertical extreme, with axis-aligned handles; these survive integer rounding with a kink of exactly 0.
- Other smooth joins need both handles at least 40 units long (kink at most 2.05° after rounding) or must be moved to an extreme.
- Round stems, alignment heights and overshoots in the program, at the knot; leave other coordinates as floats in the UFO and let the compiler round.
- Segment turning at most 90°; no inflection inside a segment; handles inside the tangent triangle; no handle shorter than 3 units; follow fontbakery's thresholds as build checks.
- Outer contours counterclockwise in the UFO.

**10. Quadratics.** Keep cu2qu's default 0.001 em. At that setting a 90° bowl becomes 2-3 quadratic segments with a true error of 0.2-0.5 units, and an S segment 6. Ship cubic outlines (CFF/CFF2) alongside TrueType where a consumer accepts them.

---

## Gaps and limits

- No METAFONT or MetaPost binary was available; verification is by published vectors and PyX's port, not by a run of `mf` or `mpost`.
- Tiller and Hanson's 1984 paper is behind a paywall and was not read; its method and performance are reported from Elber, Lee and Kim and from Levien.
- Knuth's volume E commentary was not available; Computer Modern is described from the METAFONT sources.
- The Glyphs handbook page on Fit Curve did not load; the definition comes from two Glyphs tutorials. No primary RMX Tools documentation was found.
- Iosevka's and Metapolator's issue trackers were not read; their lessons here come from source code, parameter files and READMEs.
- cu2qu has no stated analytic error bound; the `(√3/36)|Δ|/n³` bound is my derivation for a different point scheme.
- The measurements use five representative cubics, not real glyphs; the recommended tolerances should be rechecked on the first drawn glyph set.

## Files

- `/tmp/claude-0/-home-user-experiments/a86123d7-7ed9-5f3d-9952-1d096afee651/scratchpad/research/hobby_check.py`: the reference implementation and its tests (`--pyx` adds the PyX comparison).
- `/tmp/claude-0/-home-user-experiments/a86123d7-7ed9-5f3d-9952-1d096afee651/scratchpad/research/curve/experiments.py` and `/tmp/claude-0/-home-user-experiments/a86123d7-7ed9-5f3d-9952-1d096afee651/scratchpad/research/curve/experiments2.py`: the measurements of (a.5), (b.6), (c), (d) and (e); output in `/tmp/claude-0/-home-user-experiments/a86123d7-7ed9-5f3d-9952-1d096afee651/scratchpad/research/curve/experiments.out`.
- `/tmp/claude-0/-home-user-experiments/a86123d7-7ed9-5f3d-9952-1d096afee651/scratchpad/research/curve/dl/`: the downloaded sources (mf.web, mfbook.tex, plain.mf, cmbase.mf, romanl.mf, Hobby's paper, mpman.pdf, the TUGboat papers, Iosevka and fontTools sources).
- Python environment with PyX 0.18, fontTools 4.68.0, numpy and scipy: `/tmp/claude-0/-home-user-experiments/a86123d7-7ed9-5f3d-9952-1d096afee651/scratchpad/research/curve/pyxenv/.venv`.
