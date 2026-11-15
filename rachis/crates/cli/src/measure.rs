//! `rachis measure`: the numbers behind the typeface's claims, computed from its outlines and from reference fonts.
//!
//! Two kinds, ported from the prototype's `measure.py` and `report.py`. *Proportions* read the outlines with scan
//! lines: heights, stems, counters, sidebearings and the ratios legibility research states its findings in.
//! *Distances* estimate how alike two characters look at reading size: each is rendered in its cell at 14 px per
//! em, filtered for the pixel's aperture and the eye's blur, and the two images are compared.
//!
//! The distance is a screening tool. It ranks pairs and compares typefaces under one viewing model; it does not
//! predict how often a person misreads a character (`docs/research/legibility-science.md`, section f).

use std::collections::{BTreeSet, HashMap};
use std::fmt::Write as _;
use std::path::PathBuf;
use std::process::ExitCode;

use rachis_kernel::Registry;
use rachis_kernel::params::{Params, faces, master};
use tiny_skia::{FillRule, Paint, Path, PathSegment, Pixmap};

use crate::proof::{Face, OurFace, RefFace, glyph_transform};

// ---------------------------------------------------------------------------------------------------------------
// The pairs and their gates

/// A pair of strings that could be mistaken for each other, the least distance it must reach at the gate's
/// viewing condition (`None`: reported, not gated), and why it is watched.
pub(crate) struct Pair {
    pub a: &'static str,
    pub b: &'static str,
    pub gate: Option<f64>,
    pub note: &'static str,
}

const fn pair(a: &'static str, b: &'static str, gate: Option<f64>, note: &'static str) -> Pair {
    Pair { a, b, gate, note }
}

/// The default gate of a pair from mathematical notation.
const MATH: Option<f64> = Some(0.25);

/// Every watched pair. The first block is `_WATCHED` and `_WATCHED_SIGNS` of the prototype's `measure.py`, with
/// the gates of `report.py` (decision T07) and of `docs/research/legibility-science.md` ("What this means for our
/// font", items 3, 4, 5, 7 and 9). The second block is the notation of mathematics in plain text, gated at 0.25
/// where a reader must tell the two apart; pairs that mean the same sign in plain-text mathematics, or that every
/// typeface draws alike by convention, are reported without a gate (the note says which).
pub(crate) const PAIRS: &[Pair] = &[
    pair("0", "O", Some(0.30), "research item 4"),
    pair("0", "o", None, ""),
    pair("0", "8", Some(0.25), "research item 4"),
    pair("0", "D", None, ""),
    pair("O", "D", Some(0.25), "research item 4"),
    pair("O", "Q", None, ""),
    pair("1", "l", Some(0.40), "research item 3: 1 l I | pairwise"),
    pair("1", "I", Some(0.40), "research item 3"),
    pair("l", "I", Some(0.40), "research item 3"),
    pair("l", "|", Some(0.40), "research item 3"),
    pair("I", "|", Some(0.40), "research item 3"),
    pair("1", "|", Some(0.40), "research item 3 (not in report.py's gates)"),
    pair("1", "7", None, ""),
    pair("i", "l", None, ""),
    pair("i", "j", None, ""),
    pair("!", "|", None, ""),
    pair("8", "B", Some(0.25), "research item 5"),
    pair("5", "S", Some(0.25), "research item 5"),
    pair("2", "Z", None, ""),
    pair("6", "b", None, ""),
    pair("6", "G", None, ""),
    pair("9", "g", None, ""),
    pair("9", "q", None, ""),
    pair("g", "q", Some(0.35), "research item 7"),
    pair("c", "e", None, ""),
    pair("c", "o", None, ""),
    pair("e", "o", None, ""),
    pair("a", "o", None, ""),
    pair("n", "h", None, ""),
    pair("h", "b", None, ""),
    pair("n", "u", None, ""),
    pair("u", "v", None, ""),
    pair("v", "y", None, ""),
    pair("t", "f", None, ""),
    pair(".", ",", Some(0.40), "research item 9"),
    pair(":", ";", Some(0.40), "research item 9"),
    pair("'", "`", Some(0.40), "research item 9"),
    pair("'", "\"", None, ""),
    pair("(", "{", Some(0.35), "research item 9"),
    pair("(", "[", Some(0.35), "research item 9"),
    pair("}", "]", Some(0.35), "research item 9"),
    pair("{", "[", None, ""),
    pair("-", "_", None, ""),
    pair("-", "~", None, ""),
    // mathematics
    pair("v", "ν", MATH, "nu"),
    pair("u", "υ", MATH, "upsilon"),
    pair("w", "ω", MATH, "omega"),
    pair("o", "ο", None, "omicron: drawn as o in every Greek typeface"),
    pair("o", "σ", MATH, "sigma"),
    pair("ο", "σ", MATH, "omicron and sigma"),
    pair("p", "ρ", MATH, "rho"),
    pair("x", "χ", MATH, "chi"),
    pair("x", "×", MATH, "multiplication sign"),
    pair("χ", "×", MATH, ""),
    pair("a", "α", MATH, "alpha"),
    pair("n", "η", MATH, "eta"),
    pair("k", "κ", MATH, "kappa"),
    pair("i", "ι", MATH, "iota"),
    pair("t", "τ", MATH, "tau"),
    pair("B", "β", MATH, "beta"),
    pair("e", "ε", MATH, "epsilon"),
    pair("ε", "∈", MATH, "element of"),
    pair("ϵ", "∈", MATH, "lunate epsilon and element of"),
    pair("θ", "0", MATH, ""),
    pair("θ", "ϑ", MATH, "two thetas with different uses"),
    pair("φ", "ϕ", MATH, "two phis with different uses"),
    pair("l", "ℓ", MATH, "script l"),
    pair("|", "∣", None, "divides: written | in plain text"),
    pair("-", "−", MATH, "hyphen-minus and minus"),
    pair("−", "–", MATH, "minus and en dash"),
    pair("–", "—", MATH, "en and em dash"),
    pair("′", "'", MATH, "prime and apostrophe"),
    pair("∑", "Σ", MATH, "n-ary sum and Sigma"),
    pair("∏", "Π", MATH, "n-ary product and Pi"),
    pair("∆", "Δ", None, "increment: the same Delta by convention"),
    pair("∇", "▽", MATH, "nabla and white triangle"),
    pair("∂", "6", MATH, ""),
    pair("∂", "δ", MATH, ""),
    pair("·", "⋅", None, "middle dot and dot operator: the same sign in plain text"),
    pair("·", ".", MATH, ""),
    pair("∘", "°", MATH, "ring operator and degree"),
    pair("∘", "o", MATH, ""),
    pair("~", "∼", None, "tilde operator: written ~ in plain text"),
    pair("^", "∧", MATH, ""),
    pair("∨", "v", MATH, ""),
    pair("∪", "U", MATH, ""),
    pair("∩", "n", MATH, ""),
    pair("∗", "*", None, "asterisk operator: written * in plain text"),
    pair("∶", ":", None, "ratio: written : in plain text"),
    pair("∕", "/", None, "division slash: written / in plain text"),
    pair("⟨", "<", MATH, "angle bracket and less-than"),
    pair("⟨", "(", MATH, ""),
    pair("∅", "0", MATH, "empty set"),
    pair("∅", "Ø", MATH, ""),
    pair("∞", "8", MATH, ""),
    pair("ℝ", "R", MATH, "double-struck"),
    pair("ℕ", "N", MATH, "double-struck"),
    pair("ℤ", "Z", MATH, "double-struck"),
    pair("ℂ", "C", MATH, "double-struck"),
    pair("ℚ", "Q", MATH, "double-struck"),
    pair("⊂", "⊆", MATH, ""),
    pair("⊆", "⊊", MATH, ""),
    pair("≤", "<", MATH, ""),
    pair("≤", "≦", MATH, ""),
    pair("≡", "=", MATH, ""),
    pair("≈", "≅", MATH, ""),
    pair("≈", "~", MATH, ""),
    pair("→", "⟶", MATH, "arrow and long arrow"),
    pair("→", "⇒", MATH, ""),
    pair("⇒", "⇔", MATH, ""),
    pair("↦", "→", MATH, ""),
    pair("⊢", "⊨", MATH, ""),
    pair("⊥", "⟂", None, "up tack and perpendicular: the same sign by convention"),
    pair("∧", "⋀", MATH, "binary and n-ary"),
    pair("∨", "⋁", MATH, "binary and n-ary"),
    pair("∩", "⋂", MATH, "binary and n-ary"),
    pair("∪", "⋃", MATH, "binary and n-ary"),
    pair("⊕", "⨁", MATH, "binary and n-ary"),
    pair("rn", "m", MATH, "two letters against one: proportional family"),
    pair("cl", "d", MATH, "two letters against one: proportional family"),
    pair("vv", "w", MATH, "two letters against one: proportional family"),
];

/// No pair of letters and figures may come closer than this at the gate's view (the research's measurement
/// plan, item 2).
pub(crate) const ALPHANUMERIC_FLOOR: f64 = 0.20;

pub(crate) const ALPHANUMERIC: &str = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";

/// The glyph modules whose characters are the mathematical signs of the discovery table.
const SIGN_MODULES: [&str; 2] = ["operators", "arrows"];

/// Reference fonts whose distances are measured (proportions are measured for every font in `--refs`), by the
/// start of their file names.
const DISTANCE_REFS: [&str; 8] = [
    "JetBrainsMono[",
    "IBMPlexMono-Regular",
    "SourceCodePro[",
    "FiraCode[",
    "Iosevka-Regular",
    "CommitMono",
    "DejaVuSansMono.",
    "JuliaMono-Regular",
];

// ---------------------------------------------------------------------------------------------------------------
// Viewing conditions

/// A viewing condition: `px` pixels per em, a Gaussian blur of `sigma` pixels for the eye. Images are rendered
/// `SUPERSAMPLE` times finer and stay at that resolution; the pixel's aperture is a box one pixel wide.
#[derive(Clone, Copy, Debug, PartialEq)]
pub(crate) struct View {
    pub px: f64,
    pub sigma: f64,
}

pub(crate) const SUPERSAMPLE: usize = 8;

pub(crate) const VIEWS: [View; 3] =
    [View { px: 14.0, sigma: 0.6 }, View { px: 14.0, sigma: 1.0 }, View { px: 14.0, sigma: 1.5 }];

/// The view the gates are read at (`GATE_VIEW` in `report.py`).
pub(crate) const GATE: usize = 1;

impl View {
    /// The rendering size in samples per em.
    fn size(self) -> f64 {
        (self.px * SUPERSAMPLE as f64).round()
    }
}

// ---------------------------------------------------------------------------------------------------------------
// Outlines as polygons, and scan lines

pub(crate) type Polygon = Vec<(f64, f64)>;

/// The contours of `path` flattened as `measure.py` flattens them: every curve into 24 straight pieces.
pub(crate) fn polygons(path: &Path) -> Vec<Polygon> {
    const STEPS: usize = 24;
    let mut out: Vec<Polygon> = Vec::new();
    let mut cur: Polygon = Vec::new();
    for seg in path.segments() {
        let last = cur.last().copied().unwrap_or((0.0, 0.0));
        match seg {
            PathSegment::MoveTo(p) => {
                if !cur.is_empty() {
                    out.push(std::mem::take(&mut cur));
                }
                cur.push((f64::from(p.x), f64::from(p.y)));
            }
            PathSegment::LineTo(p) => cur.push((f64::from(p.x), f64::from(p.y))),
            PathSegment::QuadTo(a, c) => {
                let (a, c) = ((f64::from(a.x), f64::from(a.y)), (f64::from(c.x), f64::from(c.y)));
                for i in 1..=STEPS {
                    let t = i as f64 / STEPS as f64;
                    let u = 1.0 - t;
                    let f = |p0: f64, p1: f64, p2: f64| u * u * p0 + 2.0 * u * t * p1 + t * t * p2;
                    cur.push((f(last.0, a.0, c.0), f(last.1, a.1, c.1)));
                }
            }
            PathSegment::CubicTo(a, b, c) => {
                let (a, b) = ((f64::from(a.x), f64::from(a.y)), (f64::from(b.x), f64::from(b.y)));
                let c = (f64::from(c.x), f64::from(c.y));
                for i in 1..=STEPS {
                    let t = i as f64 / STEPS as f64;
                    let u = 1.0 - t;
                    let f = |p0: f64, p1: f64, p2: f64, p3: f64| {
                        u * u * u * p0 + 3.0 * u * u * t * p1 + 3.0 * u * t * t * p2 + t * t * t * p3
                    };
                    cur.push((f(last.0, a.0, b.0, c.0), f(last.1, a.1, b.1, c.1)));
                }
            }
            PathSegment::Close => {
                if !cur.is_empty() {
                    out.push(std::mem::take(&mut cur));
                }
            }
        }
    }
    if !cur.is_empty() {
        out.push(cur);
    }
    out
}

/// A scan line: horizontal at a height, or vertical at an x.
#[derive(Clone, Copy, Debug)]
pub(crate) enum Scan {
    Y(f64),
    X(f64),
}

/// The stretches of ink along a scan line, in order, as (start, end): where the nonzero winding number of the
/// polygons is not zero. Overlapping contours (the glyph programs' strokes overlap) count once. As in
/// `measure.py`, an edge counts only when it crosses the line strictly, so a scan line should not pass through
/// a vertex; the callers offset theirs by 0.37 units.
pub(crate) fn ink(polys: &[Polygon], scan: Scan) -> Vec<(f64, f64)> {
    let mut hits: Vec<(f64, i32)> = Vec::new();
    for poly in polys {
        for (i, &(x0, y0)) in poly.iter().enumerate() {
            let (x1, y1) = poly[(i + 1) % poly.len()];
            // (along, across): `across` is the coordinate the scan line fixes
            let (a0, c0, a1, c1, at) = match scan {
                Scan::Y(y) => (x0, y0, x1, y1, y),
                Scan::X(x) => (y0, x0, y1, x1, x),
            };
            if (c0 - at) * (c1 - at) < 0.0 {
                let along = a0 + (a1 - a0) * (at - c0) / (c1 - c0);
                hits.push((along, if c1 > c0 { 1 } else { -1 }));
            }
        }
    }
    hits.sort_by(|p, q| p.0.total_cmp(&q.0));
    let mut out = Vec::new();
    let (mut winding, mut start) = (0, 0.0);
    for (along, dir) in hits {
        let before = winding;
        winding += dir;
        if before == 0 && winding != 0 {
            start = along;
        } else if before != 0 && winding == 0 {
            out.push((start, along));
        }
    }
    out
}

/// The bounding box (x0, y0, x1, y1) of polygons.
pub(crate) fn bounds(polys: &[Polygon]) -> Option<(f64, f64, f64, f64)> {
    let mut pts = polys.iter().flatten();
    let &(x, y) = pts.next()?;
    Some(pts.fold((x, y, x, y), |(a, b, c, d), &(x, y)| (a.min(x), b.min(y), c.max(x), d.max(y))))
}

// ---------------------------------------------------------------------------------------------------------------
// Proportions

/// A face's proportions in thousandths of the em, read from its outlines; `None` where the face lacks the glyph or
/// the scan line does not find the expected strokes.
#[derive(Clone, Debug, Default)]
pub(crate) struct Proportions {
    pub x_height: Option<f64>,
    pub cap_height: Option<f64>,
    pub ascender: Option<f64>,
    pub descender: Option<f64>,
    pub advance_n: Option<f64>,
    pub advance_o: Option<f64>,
    /// Vertical stem of n, at a quarter of the x-height.
    pub n_stem: Option<f64>,
    /// Thickness of n's arch, through the middle of its counter.
    pub n_hair: Option<f64>,
    /// Thickness of o's side at half its height.
    pub o_stem: Option<f64>,
    /// Thickness of o's top through its middle.
    pub o_hair: Option<f64>,
    /// Vertical stem of H, at a quarter of the cap height.
    pub h_stem: Option<f64>,
    /// H's bar, through the middle of the advance.
    pub h_hair: Option<f64>,
    /// The white between n's stems at a quarter of the x-height.
    pub n_counter: Option<f64>,
    pub n_left: Option<f64>,
    pub n_right: Option<f64>,
    pub o_left: Option<f64>,
    pub o_right: Option<f64>,
    /// Width of the dot of i.
    pub i_dot: Option<f64>,
    /// Width of the period.
    pub period: Option<f64>,
    /// Thickness of the bar of +.
    pub op_stroke: Option<f64>,
}

impl Proportions {
    /// The white between two n's, both of n's sidebearings, over n's counter (`gap_to_counter` in `measure.py`).
    pub fn gap_to_counter(&self) -> Option<f64> {
        Some((self.n_left? + self.n_right?) / self.n_counter?)
    }

    pub fn stem_to_x_height(&self) -> Option<f64> {
        Some(self.n_stem? / self.x_height?)
    }

    pub fn x_height_to_cap(&self) -> Option<f64> {
        Some(self.x_height? / self.cap_height?)
    }
}

/// The proportions of `face`, measured as `measure.py`'s `proportions` measures them, with more of them.
pub(crate) fn proportions(face: &mut dyn Face) -> Proportions {
    let k = 1000.0 / face.upm();
    let mut polys = |c: char| -> Option<Vec<Polygon>> {
        let path = if face.has(c) { face.outline(c) } else { None }?;
        Some(polygons(&path))
    };
    let (n, o, h, x) = (polys('n'), polys('o'), polys('H'), polys('x'));
    let (b, p, i, dot, plus) = (polys('b'), polys('p'), polys('i'), polys('.'), polys('+'));
    let advance = |c: char, face: &mut dyn Face| face.has(c).then(|| face.advance_of(c));
    let (adv_n, adv_o, adv_h, adv_plus) =
        (advance('n', face), advance('o', face), advance('H', face), advance('+', face));
    let top = |ps: &Option<Vec<Polygon>>| ps.as_deref().and_then(bounds).map(|bb| bb.3);
    let xh = top(&x);
    let cap = top(&h);
    let mut out = Proportions {
        x_height: xh.map(|v| v * k),
        cap_height: cap.map(|v| v * k),
        ascender: top(&b).map(|v| v * k),
        descender: p.as_deref().and_then(bounds).map(|bb| bb.1 * k),
        advance_n: adv_n.map(|v| v * k),
        advance_o: adv_o.map(|v| v * k),
        period: dot.as_deref().and_then(bounds).map(|bb| (bb.2 - bb.0) * k),
        ..Proportions::default()
    };
    if let (Some(n), Some(xh), Some(adv)) = (&n, xh, adv_n) {
        let across = ink(n, Scan::Y(xh * 0.25 + 0.37));
        if across.len() >= 2 {
            let (first, second, last) = (across[0], across[1], across[across.len() - 1]);
            out.n_stem = Some((first.1 - first.0) * k);
            out.n_counter = Some((second.0 - first.1) * k);
            out.n_left = Some(first.0 * k);
            out.n_right = Some((adv - last.1) * k);
            let down = ink(n, Scan::X((first.1 + second.0) / 2.0 + 0.37));
            out.n_hair = down.last().map(|s| (s.1 - s.0) * k);
        }
    }
    if let (Some(o), Some(adv)) = (&o, adv_o)
        && let Some((x0, y0, x1, y1)) = bounds(o)
    {
        out.o_left = Some(x0 * k);
        out.o_right = Some((adv - x1) * k);
        out.o_stem = ink(o, Scan::Y((y0 + y1) / 2.0 + 0.37)).first().map(|s| (s.1 - s.0) * k);
        out.o_hair = ink(o, Scan::X((x0 + x1) / 2.0 + 0.37)).last().map(|s| (s.1 - s.0) * k);
    }
    if let (Some(h), Some(cap), Some(adv)) = (&h, cap, adv_h) {
        out.h_stem = ink(h, Scan::Y(cap * 0.25 + 0.37)).first().map(|s| (s.1 - s.0) * k);
        out.h_hair = ink(h, Scan::X(adv / 2.0 + 0.37)).first().map(|s| (s.1 - s.0) * k);
    }
    if let (Some(i), Some(xh)) = (&i, xh) {
        // the dot: the contour that starts highest, if it starts above the x-height
        let dot = i
            .iter()
            .filter_map(|poly| bounds(std::slice::from_ref(poly)))
            .filter(|bb| bb.1 > xh * 0.9)
            .max_by(|p, q| p.1.total_cmp(&q.1));
        out.i_dot = dot.map(|bb| (bb.2 - bb.0) * k);
    }
    if let (Some(plus), Some(adv)) = (&plus, adv_plus) {
        out.op_stroke = ink(plus, Scan::X(adv * 0.25 + 0.37)).first().map(|s| (s.1 - s.0) * k);
    }
    out
}

// ---------------------------------------------------------------------------------------------------------------
// Images and the distance

/// A filtered image, row by row, `w` samples wide.
#[derive(Clone, Debug)]
pub(crate) struct Image {
    pub w: usize,
    pub h: usize,
    pub data: Vec<f64>,
}

impl Image {
    fn zeros(w: usize, h: usize) -> Image {
        Image { w, h, data: vec![0.0; w * h] }
    }

    /// The image in a canvas `w` samples wide, moved `left` samples right; the rest is blank.
    fn widened(&self, w: usize, left: usize) -> Image {
        if w == self.w && left == 0 {
            return self.clone();
        }
        let mut out = Image::zeros(w, self.h);
        for y in 0..self.h {
            out.data[y * w + left..y * w + left + self.w].copy_from_slice(&self.data[y * self.w..(y + 1) * self.w]);
        }
        out
    }

    /// The rows and columns that hold anything but zero, as half-open ranges.
    fn support(&self) -> Option<((usize, usize), (usize, usize))> {
        let (mut r0, mut r1, mut c0, mut c1) = (usize::MAX, 0, usize::MAX, 0);
        for y in 0..self.h {
            for x in 0..self.w {
                if self.data[y * self.w + x] != 0.0 {
                    r0 = r0.min(y);
                    r1 = r1.max(y + 1);
                    c0 = c0.min(x);
                    c1 = c1.max(x + 1);
                }
            }
        }
        (r0 < r1).then_some(((r0, r1), (c0, c1)))
    }
}

/// `measure.py`'s `_gaussian`: a normalised Gaussian of standard deviation `sigma` samples, 3.5 sigma each way.
pub(crate) fn gaussian(sigma: f64) -> Vec<f64> {
    if sigma <= 0.0 {
        return vec![1.0];
    }
    let radius = (3.5 * sigma).ceil().max(1.0) as i64;
    let k: Vec<f64> = (-radius..=radius).map(|x| (-((x * x) as f64) / (2.0 * sigma * sigma)).exp()).collect();
    let sum: f64 = k.iter().sum();
    k.into_iter().map(|v| v / sum).collect()
}

/// `np.convolve(row, kernel, mode="same")` along every row (`rows`) or every column, zero outside the image.
fn convolve(img: &Image, kernel: &[f64], rows: bool) -> Image {
    let (len, count) = if rows { (img.w, img.h) } else { (img.h, img.w) };
    let m = kernel.len();
    // the "same" window starts (m - 1) / 2 into the full convolution
    let off = ((m - 1) / 2) as i64;
    let mut out = Image::zeros(img.w, img.h);
    let at = |line: usize, i: usize| if rows { line * img.w + i } else { i * img.w + line };
    for line in 0..count {
        for i in 0..len {
            let mut acc = 0.0;
            for (j, &kv) in kernel.iter().enumerate() {
                let src = i as i64 + off - j as i64;
                if src >= 0 && (src as usize) < len {
                    acc += img.data[at(line, src as usize)] * kv;
                }
            }
            out.data[at(line, i)] = acc;
        }
    }
    out
}

/// `image` as `Renderer.image` filters it: the pixel's aperture (a box one pixel wide), then the eye (a Gaussian),
/// each along the rows and then the columns.
pub(crate) fn filter(image: &Image, view: View) -> Image {
    let boxk = vec![1.0 / SUPERSAMPLE as f64; SUPERSAMPLE];
    let gauss = gaussian(view.sigma * SUPERSAMPLE as f64);
    let mut a = convolve(image, &boxk, true);
    a = convolve(&a, &boxk, false);
    a = convolve(&a, &gauss, true);
    convolve(&a, &gauss, false)
}

/// How two images compare: 0 when they are identical, sqrt(2) when they share no ink. With `shift`, the least
/// value over displacements of the second of up to one pixel each way in half-pixel steps, wrapping around as
/// `np.roll` does (`Renderer.distance`). Both images must have the same size.
pub(crate) fn distance(a: &Image, b: &Image, shift: bool) -> f64 {
    assert_eq!((a.w, a.h), (b.w, b.h), "images of different sizes");
    let (Some(sa), Some(sb)) = (a.support(), b.support()) else {
        return if a.support().is_none() && b.support().is_none() { 0.0 } else { std::f64::consts::SQRT_2 };
    };
    let energy = |img: &Image, ((r0, r1), (c0, c1)): ((usize, usize), (usize, usize))| {
        let mut e = 0.0;
        for y in r0..r1 {
            for x in c0..c1 {
                let v = img.data[y * img.w + x];
                e += v * v;
            }
        }
        e
    };
    let (ea, eb) = (energy(a, sa), energy(b, sb));
    let norm = ((ea + eb) / 2.0).sqrt();
    if norm == 0.0 {
        return 0.0;
    }
    let half = (SUPERSAMPLE / 2) as i64;
    let steps: Vec<i64> = if shift { vec![-2 * half, -half, 0, half, 2 * half] } else { vec![0] };
    let (w, h) = (a.w as i64, a.h as i64);
    let ((ar0, ar1), (ac0, ac1)) = sa;
    let ((br0, br1), (bc0, bc1)) = sb;
    let mut best = f64::INFINITY;
    for &dx in &steps {
        for &dy in &steps {
            // the cross term of ||a - roll(b)||^2: moved[y][x] = b[(y - dy) mod h][(x - dx) mod w]
            let mut cross = 0.0;
            for y in ar0..ar1 {
                let by = (y as i64 - dy).rem_euclid(h) as usize;
                if by < br0 || by >= br1 {
                    continue;
                }
                for x in ac0..ac1 {
                    let bx = (x as i64 - dx).rem_euclid(w) as usize;
                    if bx < bc0 || bx >= bc1 {
                        continue;
                    }
                    cross += a.data[y * a.w + x] * b.data[by * b.w + bx];
                }
            }
            let d = (ea + eb - 2.0 * cross).max(0.0).sqrt() / norm;
            best = best.min(d);
        }
    }
    best
}

/// How a pair of images is placed in their common box.
#[derive(Clone, Copy, Debug, PartialEq)]
pub(crate) enum Align {
    /// At the same origin, as a terminal sets them (the fixed-pitch family; `measure.py`).
    Origin,
    /// With the centres of their advances together (the proportional family and reference fonts).
    Centre,
}

/// The outlines and advances of the characters a measurement needs from one face, in font units.
pub(crate) struct Glyphs {
    pub upm: f64,
    pub align: Align,
    /// Every character the face has, with its advance and outline (`None` when it is blank).
    pub chars: HashMap<char, (f64, Option<Path>)>,
    /// The kerning between the neighbours inside the watched strings of more than one character, in font
    /// units: a string is measured as the fonts set it.
    pub kerns: HashMap<(char, char), f64>,
}

impl Glyphs {
    pub fn load(face: &mut dyn Face, align: Align, wanted: impl IntoIterator<Item = char>) -> Glyphs {
        let mut chars = HashMap::new();
        for c in wanted {
            if face.has(c) && !chars.contains_key(&c) {
                chars.insert(c, (face.advance_of(c), face.outline(c)));
            }
        }
        let mut kerns = HashMap::new();
        for text in PAIRS.iter().flat_map(|p| [p.a, p.b]) {
            let cs: Vec<char> = text.chars().collect();
            for pair in cs.windows(2) {
                let k = face.kern(pair[0], pair[1]);
                if k != 0.0 {
                    kerns.insert((pair[0], pair[1]), k);
                }
            }
        }
        Glyphs { upm: face.upm(), align, chars, kerns }
    }

    /// The kerning before each character of `text`, in font units: 0 before the first.
    fn kerning(&self, text: &str) -> Vec<f64> {
        let cs: Vec<char> = text.chars().collect();
        (0..cs.len())
            .map(|i| if i == 0 { 0.0 } else { self.kerns.get(&(cs[i - 1], cs[i])).copied().unwrap_or(0.0) })
            .collect()
    }

    pub fn has(&self, text: &str) -> bool {
        text.chars().all(|c| self.chars.contains_key(&c))
    }

    /// `text` rendered at `view` with the glyphs' own advances and the face's kerning, and filtered, in a box as wide as its advance or
    /// 0.6 em, whichever is wider, with 3 pixels on each side; the baseline 1.15 em from the top of a box 1.6 em
    /// tall (`Renderer.image`). `None` when the face lacks a character.
    pub fn image(&self, text: &str, view: View) -> Option<Image> {
        let size = view.size();
        let k = size / self.upm;
        let kerning = self.kerning(text);
        let advance: f64 = (text.chars().map(|c| self.chars.get(&c).map(|g| g.0)).sum::<Option<f64>>()?
            + kerning.iter().sum::<f64>())
            * k;
        let mut cell = (advance.round().max((0.6 * size).round())) as usize;
        if self.align == Align::Centre && cell.is_multiple_of(2) {
            // every box odd, so that two boxes centre on the same sample
            cell += 1;
        }
        let pad = 3 * SUPERSAMPLE;
        let (w, h) = (cell + 2 * pad, (1.6 * size).round() as usize);
        let baseline = (1.15 * size).round();
        let mut x = pad as f64;
        if self.align == Align::Centre {
            x += (cell as f64 - advance) / 2.0;
        }
        let mut pix = Pixmap::new(w as u32, h as u32)?;
        let mut paint = Paint::default();
        paint.set_color_rgba8(0, 0, 0, 255);
        paint.anti_alias = true;
        for (c, kern) in text.chars().zip(kerning) {
            x += kern * k;
            let (adv, path) = &self.chars[&c];
            if let Some(path) = path {
                pix.fill_path(path, &paint, FillRule::Winding, glyph_transform(k, x, baseline), None);
            }
            x += adv * k;
        }
        let raw = Image { w, h, data: pix.pixels().iter().map(|p| f64::from(p.alpha()) / 255.0).collect() };
        Some(filter(&raw, view))
    }
}

/// The distance between two images of one face, in their common box.
pub(crate) fn pair_distance(a: &Image, b: &Image, align: Align) -> f64 {
    let w = a.w.max(b.w);
    let place = |img: &Image| match align {
        Align::Origin => img.widened(w, 0),
        Align::Centre => img.widened(w, (w - img.w) / 2),
    };
    distance(&place(a), &place(b), true)
}

/// `f` over `items` on every core.
fn par_map<T: Sync, R: Send>(items: &[T], f: impl Fn(&T) -> R + Sync) -> Vec<R> {
    let threads = std::thread::available_parallelism().map_or(1, |n| n.get()).min(items.len().max(1));
    let chunk = items.len().div_ceil(threads).max(1);
    std::thread::scope(|s| {
        let handles: Vec<_> =
            items.chunks(chunk).map(|part| s.spawn(|| part.iter().map(&f).collect::<Vec<R>>())).collect();
        handles.into_iter().flat_map(|h| h.join().expect("a measuring thread panicked")).collect()
    })
}

/// The images of `texts` at `view`, keyed by text; texts the face lacks are left out.
fn images(glyphs: &Glyphs, texts: &BTreeSet<String>, view: View) -> HashMap<String, Image> {
    let list: Vec<&String> = texts.iter().filter(|t| glyphs.has(t)).collect();
    let imgs = par_map(&list, |t| glyphs.image(t, view));
    list.into_iter().cloned().zip(imgs).filter_map(|(t, i)| Some((t, i?))).collect()
}

/// The distance of every watched pair at `view`; `None` where the face lacks a character.
fn watched(glyphs: &Glyphs, view: View) -> Vec<Option<f64>> {
    let texts: BTreeSet<String> = PAIRS.iter().flat_map(|p| [p.a.to_string(), p.b.to_string()]).collect();
    let imgs = images(glyphs, &texts, view);
    par_map(PAIRS, |p| Some(pair_distance(imgs.get(p.a)?, imgs.get(p.b)?, glyphs.align)))
}

/// Every unordered pair of `chars` that `keep` accepts, with its distance at `view`, closest first
/// (`all_pairs` in `measure.py`).
fn all_pairs(glyphs: &Glyphs, chars: &[char], view: View, keep: impl Fn(char, char) -> bool) -> Vec<(f64, char, char)> {
    let texts: BTreeSet<String> = chars.iter().map(char::to_string).collect();
    let imgs = images(glyphs, &texts, view);
    let have: Vec<char> = chars.iter().copied().filter(|c| imgs.contains_key(&c.to_string())).collect();
    let pairs: Vec<(char, char)> = have
        .iter()
        .enumerate()
        .flat_map(|(i, &a)| have[i + 1..].iter().map(move |&b| (a, b)))
        .filter(|&(a, b)| keep(a, b))
        .collect();
    let mut out =
        par_map(&pairs, |&(a, b)| (pair_distance(&imgs[&a.to_string()], &imgs[&b.to_string()], glyphs.align), a, b));
    out.sort_by(|p, q| p.0.total_cmp(&q.0).then(p.1.cmp(&q.1)).then(p.2.cmp(&q.2)));
    out
}

// ---------------------------------------------------------------------------------------------------------------
// The command

const USAGE: &str =
    "usage: rachis measure [--master NAME] [--refs DIR] [--out FILE.md] [--gate] [--distance-refs PREFIX...]";

struct Opts {
    master: Option<String>,
    refs: Option<PathBuf>,
    out: Option<PathBuf>,
    gate: bool,
    distance_refs: Vec<String>,
}

impl Opts {
    fn parse(args: &[String]) -> Result<Opts, String> {
        let mut opts = Opts {
            master: None,
            refs: None,
            out: None,
            gate: false,
            distance_refs: DISTANCE_REFS.map(String::from).to_vec(),
        };
        let mut i = 0;
        while i < args.len() {
            let flag = args[i].as_str();
            i += 1;
            let mut value = || {
                i += 1;
                args.get(i - 1).cloned().ok_or_else(|| format!("{flag} needs a value"))
            };
            match flag {
                "--master" => opts.master = Some(value()?),
                "--refs" => opts.refs = Some(PathBuf::from(value()?)),
                "--out" | "-o" => opts.out = Some(PathBuf::from(value()?)),
                "--gate" => opts.gate = true,
                "--distance-refs" => {
                    opts.distance_refs.clear();
                    while i < args.len() && !args[i].starts_with("--") {
                        opts.distance_refs.push(args[i].clone());
                        i += 1;
                    }
                }
                _ => return Err(format!("unknown argument {flag:?}")),
            }
        }
        Ok(opts)
    }
}

/// What was measured of one of our masters.
struct Ours {
    params: Params,
    props: Proportions,
    /// Per view, per watched pair.
    pairs: Option<[Vec<Option<f64>>; 3]>,
    alphanumeric: Vec<(f64, char, char)>,
    signs: Vec<(f64, char, char)>,
    greek: Vec<(f64, char, char)>,
}

/// What was measured of a reference font.
struct Reference {
    label: String,
    props: Proportions,
    /// At the gate's view, per watched pair; `None` when its distances were not measured.
    pairs: Option<Vec<Option<f64>>>,
}

/// One section of the document: a family, its masters' proportions and the masters whose distances are measured.
struct Section {
    family: &'static str,
    table: Vec<Ours>,
}

pub fn run(registry: &Registry, args: &[String]) -> ExitCode {
    let opts = match Opts::parse(args) {
        Ok(o) => o,
        Err(e) => {
            eprintln!("rachis measure: {e}\n{USAGE}");
            return ExitCode::FAILURE;
        }
    };
    let mut sections = Vec::new();
    match &opts.master {
        Some(name) => {
            let Some(p) = master(name) else {
                eprintln!("rachis measure: no master named {name:?}");
                return ExitCode::FAILURE;
            };
            let family = if p.mono { "Rachis Mono" } else { "Rachis" };
            sections.push(Section { family, table: vec![measure_master(registry, &p, true)] });
        }
        None => {
            for face in faces().into_iter().filter(|f| !f.italic) {
                let table = face
                    .masters
                    .iter()
                    .map(|p| {
                        eprintln!("measuring {}", p.name);
                        measure_master(registry, p, p.wght == 400.0)
                    })
                    .collect();
                sections.push(Section { family: face.family, table });
            }
        }
    }
    let refs = match &opts.refs {
        Some(dir) => match references(dir, &opts.distance_refs) {
            Ok(r) => r,
            Err(e) => {
                eprintln!("rachis measure: cannot read {}: {e}", dir.display());
                return ExitCode::FAILURE;
            }
        },
        None => Vec::new(),
    };
    let failures = gate_failures(&sections);
    let doc = document(&sections, &refs, &opts, &failures);
    match &opts.out {
        Some(path) => {
            if let Err(e) = std::fs::write(path, &doc) {
                eprintln!("rachis measure: cannot write {}: {e}", path.display());
                return ExitCode::FAILURE;
            }
            eprintln!("wrote {}", path.display());
        }
        None => {
            let _ = std::io::Write::write_all(&mut std::io::stdout(), doc.as_bytes());
        }
    }
    if opts.gate && !failures.is_empty() {
        for f in &failures {
            eprintln!("FAIL: {f}");
        }
        eprintln!("{} gates fail", failures.len());
        return ExitCode::FAILURE;
    }
    ExitCode::SUCCESS
}

/// The characters every measurement of a face may need.
fn wanted_chars(registry: &Registry) -> BTreeSet<char> {
    let mut out: BTreeSet<char> = ALPHANUMERIC.chars().collect();
    out.extend(PAIRS.iter().flat_map(|p| p.a.chars().chain(p.b.chars())));
    out.extend(sign_chars(registry));
    out.extend(greek_chars(registry));
    out
}

/// The encoded glyphs of the sign modules, as characters, leaving out marks and blank glyphs.
fn sign_chars(registry: &Registry) -> Vec<char> {
    registry
        .specs
        .iter()
        .filter(|s| SIGN_MODULES.contains(&s.module) && !s.opt.mark)
        .flat_map(|s| s.unicodes.iter().filter_map(|&u| char::from_u32(u)))
        .filter(|c| !c.is_whitespace())
        .collect()
}

fn greek_chars(registry: &Registry) -> Vec<char> {
    registry
        .specs
        .iter()
        .filter(|s| s.module == "greek" && !s.opt.mark)
        .flat_map(|s| s.unicodes.iter().filter_map(|&u| char::from_u32(u)))
        .collect()
}

fn is_greek(c: char) -> bool {
    ('\u{0370}'..='\u{03FF}').contains(&c) || c == '\u{00B5}' || c == '\u{2126}'
}

/// Proportions of a master, and with `distances` its watched pairs at every view and its closest pairs.
fn measure_master(registry: &Registry, p: &Params, distances: bool) -> Ours {
    let mut face = OurFace::new(registry, p.clone());
    let props = proportions(&mut face);
    let mut ours = Ours { params: p.clone(), props, pairs: None, alphanumeric: vec![], signs: vec![], greek: vec![] };
    if !distances {
        return ours;
    }
    let align = if p.mono { Align::Origin } else { Align::Centre };
    let glyphs = Glyphs::load(&mut face, align, wanted_chars(registry));
    ours.pairs = Some(VIEWS.map(|v| watched(&glyphs, v)));
    let view = VIEWS[GATE];
    let alnum: Vec<char> = ALPHANUMERIC.chars().collect();
    ours.alphanumeric = all_pairs(&glyphs, &alnum, view, |_, _| true);
    ours.signs = all_pairs(&glyphs, &sign_chars(registry), view, |_, _| true);
    // Latin first, so that a Greek letter drawn as a Latin one is listed as the Latin one
    let mut letters: Vec<char> = ALPHANUMERIC.chars().collect();
    letters.extend(greek_chars(registry));
    ours.greek = all_pairs(&glyphs, &letters, view, |a, b| is_greek(a) || is_greek(b));
    ours
}

/// Every .ttf and .otf in `dir`: proportions of all, distances of those whose names start with a prefix in
/// `distance_refs`.
fn references(dir: &std::path::Path, distance_refs: &[String]) -> Result<Vec<Reference>, String> {
    let mut files: Vec<PathBuf> = std::fs::read_dir(dir)
        .map_err(|e| e.to_string())?
        .filter_map(|e| e.ok().map(|e| e.path()))
        .filter(|p| p.extension().is_some_and(|x| x == "ttf" || x == "otf"))
        .collect();
    files.sort();
    let mut out = Vec::new();
    for path in files {
        let name = path.file_name().map(|n| n.to_string_lossy().into_owned()).unwrap_or_default();
        let label = path.file_stem().map(|n| n.to_string_lossy().into_owned()).unwrap_or_default();
        let mut face = match RefFace::load(&path, label.clone()) {
            Ok(f) => f,
            Err(e) => {
                eprintln!("note: cannot read {}: {e}", path.display());
                continue;
            }
        };
        let props = proportions(&mut face);
        let pairs = distance_refs.iter().any(|p| name.starts_with(p.as_str())).then(|| {
            eprintln!("measuring {label}");
            let texts = PAIRS.iter().flat_map(|p| p.a.chars().chain(p.b.chars()));
            let glyphs = Glyphs::load(&mut face, Align::Centre, texts);
            watched(&glyphs, VIEWS[GATE])
        });
        out.push(Reference { label, props, pairs });
    }
    Ok(out)
}

/// Every gate that a measured Regular fails, in words.
fn gate_failures(sections: &[Section]) -> Vec<String> {
    let mut out = Vec::new();
    for ours in sections.iter().flat_map(|s| &s.table) {
        let Some(pairs) = &ours.pairs else {
            continue;
        };
        for (p, d) in PAIRS.iter().zip(&pairs[GATE]) {
            if let (Some(gate), Some(d)) = (p.gate, d)
                && *d < gate
            {
                out.push(format!("{}: {} {} at {} < {}", ours.params.name, p.a, p.b, below(*d, gate), sig3(gate)));
            }
        }
        for &(d, a, b) in ours.alphanumeric.iter().take_while(|e| e.0 < ALPHANUMERIC_FLOOR) {
            out.push(format!(
                "{}: {a} {b} at {} < {} (letters and figures)",
                ours.params.name,
                below(d, ALPHANUMERIC_FLOOR),
                sig3(ALPHANUMERIC_FLOOR)
            ));
        }
    }
    out
}

// ---------------------------------------------------------------------------------------------------------------
// The document

/// `d`, a distance under `gate`, to three significant figures, or to four when three would round it up to `gate`.
fn below(d: f64, gate: f64) -> String {
    if sig3(d) == sig3(gate) { format!("{d:.4}") } else { sig3(d) }
}

/// `x` to three significant figures.
pub(crate) fn sig3(x: f64) -> String {
    if x == 0.0 || !x.is_finite() {
        return format!("{x}");
    }
    let digits = 2 - x.abs().log10().floor() as i32;
    if digits >= 0 {
        let s = format!("{x:.*}", digits as usize);
        // rounding can carry into a fourth figure (0.9996 -> 1.000)
        let again = 2 - s.parse::<f64>().unwrap_or(x).abs().log10().floor() as i32;
        if again < digits && again >= 0 { format!("{x:.*}", again as usize) } else { s }
    } else {
        let unit = 10f64.powi(-digits);
        format!("{:.0}", (x / unit).round() * unit)
    }
}

fn cell(v: Option<f64>) -> String {
    v.map_or_else(|| "–".to_string(), sig3)
}

/// A string as Markdown code inside a table.
fn code(s: &str) -> String {
    let s = s.replace('|', "\\|");
    if s.contains('`') { format!("`` {s} ``") } else { format!("`{s}`") }
}

fn table(out: &mut String, head: &[String], rows: &[Vec<String>]) {
    let _ = writeln!(out, "| {} |", head.join(" | "));
    let _ = writeln!(out, "|{}", "---|".repeat(head.len()));
    for r in rows {
        let _ = writeln!(out, "| {} |", r.join(" | "));
    }
    out.push('\n');
}

fn proportions_tables(out: &mut String, rows: &[(String, &Proportions)]) {
    let head1: Vec<String> = [
        "",
        "x-height",
        "cap height",
        "ascender",
        "descender",
        "advance n",
        "advance o",
        "n left",
        "n right",
        "o left",
        "o right",
        "n counter",
        "dot of i",
        "period",
    ]
    .map(String::from)
    .to_vec();
    let rows1: Vec<Vec<String>> = rows
        .iter()
        .map(|(label, p)| {
            let mut r = vec![label.clone()];
            r.extend(
                [
                    p.x_height,
                    p.cap_height,
                    p.ascender,
                    p.descender,
                    p.advance_n,
                    p.advance_o,
                    p.n_left,
                    p.n_right,
                    p.o_left,
                    p.o_right,
                    p.n_counter,
                    p.i_dot,
                    p.period,
                ]
                .map(cell),
            );
            r
        })
        .collect();
    table(out, &head1, &rows1);
    let head2: Vec<String> = [
        "",
        "n stem",
        "n arch",
        "o side",
        "o top",
        "H stem",
        "H bar",
        "+ bar",
        "stem / x-height",
        "x-height / cap",
        "gap / counter",
    ]
    .map(String::from)
    .to_vec();
    let rows2: Vec<Vec<String>> = rows
        .iter()
        .map(|(label, p)| {
            let mut r = vec![label.clone()];
            r.extend(
                [
                    p.n_stem,
                    p.n_hair,
                    p.o_stem,
                    p.o_hair,
                    p.h_stem,
                    p.h_hair,
                    p.op_stroke,
                    p.stem_to_x_height(),
                    p.x_height_to_cap(),
                    p.gap_to_counter(),
                ]
                .map(cell),
            );
            r
        })
        .collect();
    table(out, &head2, &rows2);
}

fn command_line(opts: &Opts) -> String {
    let mut cmd = String::from("cargo run -q -p rachis -- measure");
    if let Some(m) = &opts.master {
        let _ = write!(cmd, " --master '{m}'");
    }
    if let Some(r) = &opts.refs {
        // the directory is the reader's own: its place on this machine says nothing
        let _ = r;
        let _ = write!(cmd, " --refs <directory of reference fonts>");
    }
    if opts.distance_refs != DISTANCE_REFS.map(String::from).to_vec() {
        let _ = write!(cmd, " --distance-refs {}", opts.distance_refs.join(" "));
    }
    if let Some(o) = &opts.out {
        let _ = write!(cmd, " --out {}", o.display());
    }
    cmd
}

const METHOD: &str = "\
**Method.** Proportions are read from the outlines with scan lines through the contours, each curve flattened \
into 24 straight pieces; where contours overlap, ink is where the nonzero winding number is not zero. They are \
in thousandths of the em: x-height, cap height, ascender and descender are the tops of x, H and b and the bottom \
of p; n's stems, counter and sidebearings are read at a quarter of the x-height, n's arch through the middle of \
its counter, o's side at half its height and its top through its middle, H's stem at a quarter of the cap height \
and its bar through the middle of its advance, the bar of + a quarter of the way across its advance; the dot of i \
and the period are their widths. Gap / counter is n's two sidebearings over its counter.

The distance of two characters is computed as the prototype's `measure.py` computes it. Each is rendered at 14 \
pixels per em, eight times supersampled, into a box as wide as its advance or 0.6 em, whichever is wider, with \
3 pixels each side, and filtered at that resolution by a box one pixel wide (the pixel's aperture) and a Gaussian \
of sigma pixels (the eye: 0.6 px is ordinary optics, 1.0 px where the detail reading uses runs out, 1.5 px dark \
themes, defocus and a glance). Then D = ||A − B|| / sqrt((||A||² + ||B||²) / 2): 0 for identical images, \
sqrt(2) ≈ 1.41 for images that share no ink, and the least value over displacements of up to one pixel each way \
in half-pixel steps, since a reader does not know where a character sits to the pixel. In the fixed-pitch family \
both are placed at the same origin, as a terminal sets them; in the proportional family and in the reference \
fonts the centres of their advances coincide. Strings of two letters are set with their real advances. Gates are \
read at 14 px, sigma 1.0 px.

**Limits.** The distance is a screening tool for comparing pairs and typefaces under one viewing model. It does \
not predict how often a person misreads a character: against the only human confusion data we could test it on \
(Mueller and Weidemann's letter matrices), its rank correlation was at most 0.33 \
(`docs/research/legibility-science.md`, section f). A gate passed is a pair that is no closer than the threshold \
under this model; it is not a legibility claim. Nothing here was tested on people reading code.";

fn document(sections: &[Section], refs: &[Reference], opts: &Opts, failures: &[String]) -> String {
    let mut out = String::new();
    let _ = writeln!(out, "# Measurements\n");
    let _ = writeln!(out, "Generated by `rachis measure`; regenerate with:\n\n```\n{}\n```\n", command_line(opts));
    let _ = writeln!(out, "{METHOD}\n");
    if failures.is_empty() {
        let _ = writeln!(out, "**Gates.** Every gate passes.\n");
    } else {
        let _ = writeln!(out, "**Gates.** {} fail:\n", failures.len());
        for f in failures {
            let _ = writeln!(out, "- {}", f.replace('|', "\\|"));
        }
        out.push('\n');
    }
    for s in sections {
        let _ = writeln!(out, "## {}\n", s.family);
        let _ = writeln!(out, "### Proportions\n");
        let mut rows: Vec<(String, &Proportions)> =
            s.table.iter().map(|o| (o.params.name.to_string(), &o.props)).collect();
        if s.table.iter().any(|o| o.params.mono) {
            rows.extend(refs.iter().map(|r| (r.label.clone(), &r.props)));
        }
        proportions_tables(&mut out, &rows);
        let measured: Vec<&Ours> = s.table.iter().filter(|o| o.pairs.is_some()).collect();
        if measured.is_empty() {
            continue;
        }
        let with_refs: Vec<&Reference> = if s.table.iter().any(|o| o.params.mono) {
            refs.iter().filter(|r| r.pairs.is_some()).collect()
        } else {
            vec![]
        };
        let _ = writeln!(out, "### Watched pairs\n");
        let _ = writeln!(
            out,
            "Distances at 14 px for blurs of 0.6, 1.0 and 1.5 px; the gate is read at 1.0 px. **Bold** marks a failed \
             gate; \"missing\" a character the master does not have yet.{}\n",
            if with_refs.is_empty() {
                ""
            } else {
                " Reference fonts at 1.0 px, with the centres of their advances together."
            }
        );
        let mut head = vec!["pair".to_string(), "gate".to_string()];
        for o in &measured {
            for v in VIEWS {
                head.push(format!("{} σ {:.1}", o.params.name, v.sigma));
            }
        }
        head.extend(with_refs.iter().map(|r| r.label.clone()));
        head.push("note".into());
        let rows: Vec<Vec<String>> = PAIRS
            .iter()
            .enumerate()
            .map(|(i, p)| {
                let mut r = vec![format!("{} {}", code(p.a), code(p.b)), p.gate.map_or_else(String::new, sig3)];
                for o in &measured {
                    let pairs = o.pairs.as_ref().expect("measured");
                    for (vi, per_view) in pairs.iter().enumerate() {
                        r.push(match per_view[i] {
                            None => "missing".into(),
                            Some(d) if vi == GATE && p.gate.is_some_and(|g| d < g) => format!("**{}**", sig3(d)),
                            Some(d) => sig3(d),
                        });
                    }
                }
                for rf in &with_refs {
                    r.push(cell(rf.pairs.as_ref().and_then(|ps| ps[i])));
                }
                r.push(p.note.replace('|', "\\|"));
                r
            })
            .collect();
        table(&mut out, &head, &rows);
        for o in &measured {
            let _ = writeln!(out, "### Closest pairs in {} (14 px, blur 1.0 px)\n", o.params.name);
            let alnum: Vec<f64> = o.alphanumeric.iter().map(|e| e.0).collect();
            let under = alnum.iter().filter(|&&d| d < ALPHANUMERIC_FLOOR).count();
            let _ = writeln!(
                out,
                "All {} pairs of the letters and figures: {} under {}, median {}. The ten closest of them, of the \
                 mathematical signs (the glyph modules {}: {} pairs) and of Greek letters against Latin letters, \
                 figures and each other ({} pairs). Pairs drawn identically (D = 0: a Greek capital that is the \
                 Latin one, a sign that is another's glyph) are listed once, by the first of them: {} and {}.\n",
                alnum.len(),
                under,
                sig3(ALPHANUMERIC_FLOOR),
                cell(median(&alnum)),
                SIGN_MODULES.join(" and "),
                o.signs.len(),
                o.greek.len(),
                same(&o.signs),
                same(&o.greek),
            );
            let head: Vec<String> =
                ["", "letters and figures", "D", "signs", "D", "Greek", "D"].map(String::from).to_vec();
            let pick = |list: &[(f64, char, char)], i: usize| -> [String; 2] {
                list.get(i).map_or_else(
                    || [String::new(), String::new()],
                    |&(d, a, b)| [format!("{} {}", code(&a.to_string()), code(&b.to_string())), sig3(d)],
                )
            };
            let rows: Vec<Vec<String>> = (0..10)
                .map(|i| {
                    let mut r = vec![(i + 1).to_string()];
                    r.extend(pick(&o.alphanumeric, i));
                    r.extend(pick(&distinct(&o.signs), i));
                    r.extend(pick(&distinct(&o.greek), i));
                    r
                })
                .collect();
            table(&mut out, &head, &rows);
        }
    }
    out
}

/// The pairs of `list` that are not drawn identically, with every character that is drawn as an earlier one (the
/// second of a pair at distance 0) left out, so that a glyph shared by two code points is listed once.
fn distinct(list: &[(f64, char, char)]) -> Vec<(f64, char, char)> {
    let copies: BTreeSet<char> = list.iter().filter(|e| e.0 == 0.0).map(|e| e.2).collect();
    list.iter().copied().filter(|e| e.0 > 0.0 && !copies.contains(&e.1) && !copies.contains(&e.2)).collect()
}

/// The pairs of `list` drawn identically, in words.
fn same(list: &[(f64, char, char)]) -> String {
    let same: Vec<String> = list.iter().filter(|e| e.0 == 0.0).map(|&(_, a, b)| format!("{a}{b}")).collect();
    if same.is_empty() { "none".into() } else { same.join(" ").replace('|', "\\|") }
}

fn median(v: &[f64]) -> Option<f64> {
    if v.is_empty() {
        return None;
    }
    let mut s = v.to_vec();
    s.sort_by(f64::total_cmp);
    let n = s.len();
    Some(if n % 2 == 1 { s[n / 2] } else { (s[n / 2 - 1] + s[n / 2]) / 2.0 })
}

// ---------------------------------------------------------------------------------------------------------------

#[cfg(test)]
mod tests {
    use super::*;
    use tiny_skia::PathBuilder;

    fn rect(pb: &mut PathBuilder, x0: f32, y0: f32, x1: f32, y1: f32) {
        pb.move_to(x0, y0);
        pb.line_to(x1, y0);
        pb.line_to(x1, y1);
        pb.line_to(x0, y1);
        pb.close();
    }

    /// An n made of two stems 80 wide and an arch 60 thick, overlapping the stems, in a 600 advance.
    fn n_like() -> Vec<Polygon> {
        let mut pb = PathBuilder::new();
        rect(&mut pb, 100.0, 0.0, 180.0, 500.0);
        rect(&mut pb, 420.0, 0.0, 500.0, 500.0);
        rect(&mut pb, 100.0, 440.0, 500.0, 500.0);
        polygons(&pb.finish().unwrap())
    }

    #[test]
    fn scan_lines_find_stems_counter_and_arch() {
        let n = n_like();
        let across = ink(&n, Scan::Y(125.37));
        assert_eq!(across, vec![(100.0, 180.0), (420.0, 500.0)]);
        // through the overlap the arch and the stems are one stretch of ink
        assert_eq!(ink(&n, Scan::Y(470.37)), vec![(100.0, 500.0)]);
        let down = ink(&n, Scan::X(300.37));
        assert_eq!(down.len(), 1);
        assert!((down[0].1 - down[0].0 - 60.0).abs() < 1e-9);
        assert!(ink(&n, Scan::Y(600.0)).is_empty());
    }

    #[test]
    fn a_counter_drawn_the_other_way_is_white() {
        // an o as a square with a square hole wound the other way
        let mut pb = PathBuilder::new();
        rect(&mut pb, 0.0, 0.0, 300.0, 300.0);
        pb.move_to(50.0, 50.0);
        pb.line_to(50.0, 250.0);
        pb.line_to(250.0, 250.0);
        pb.line_to(250.0, 50.0);
        pb.close();
        let o = polygons(&pb.finish().unwrap());
        assert_eq!(ink(&o, Scan::Y(150.37)), vec![(0.0, 50.0), (250.0, 300.0)]);
    }

    #[test]
    fn curves_are_flattened_into_24_pieces() {
        let mut pb = PathBuilder::new();
        pb.move_to(0.0, 0.0);
        pb.cubic_to(0.0, 100.0, 100.0, 100.0, 100.0, 0.0);
        pb.quad_to(50.0, -50.0, 0.0, 0.0);
        pb.close();
        let polys = polygons(&pb.finish().unwrap());
        assert_eq!(polys.len(), 1);
        assert_eq!(polys[0].len(), 1 + 24 + 24);
        // the cubic's top is at 75
        let (_, y0, _, y1) = bounds(&polys).unwrap();
        assert!((y1 - 75.0).abs() < 0.2 && (y0 + 25.0).abs() < 0.2, "{y0} {y1}");
    }

    #[test]
    fn the_gaussian_matches_measure_py() {
        let k = gaussian(8.0);
        assert_eq!(k.len(), 2 * 28 + 1);
        assert!((k.iter().sum::<f64>() - 1.0).abs() < 1e-12);
        assert_eq!(gaussian(0.0), vec![1.0]);
        // np.convolve([0,0,1,0,0], [1,1,1,1]/4, "same") = [0, 0.25, 0.25, 0.25, 0.25]
        let img = Image { w: 5, h: 1, data: vec![0.0, 0.0, 1.0, 0.0, 0.0] };
        let out = convolve(&img, &[0.25; 4], true);
        assert_eq!(out.data, vec![0.0, 0.25, 0.25, 0.25, 0.25]);
    }

    fn blob(w: usize, h: usize, x0: usize, x1: usize, y0: usize, y1: usize) -> Image {
        let mut img = Image::zeros(w, h);
        for y in y0..y1 {
            for x in x0..x1 {
                img.data[y * w + x] = 1.0;
            }
        }
        img
    }

    #[test]
    fn distance_is_zero_for_the_same_image_and_symmetric() {
        let view = VIEWS[GATE];
        let a = filter(&blob(80, 60, 10, 30, 10, 40), view);
        let b = filter(&blob(80, 60, 25, 50, 15, 30), view);
        assert_eq!(distance(&a, &a, true), 0.0);
        assert_eq!(distance(&a, &a, false), 0.0);
        let (ab, ba) = (distance(&a, &b, false), distance(&b, &a, false));
        assert!((ab - ba).abs() < 1e-12, "{ab} {ba}");
        let (ab, ba) = (distance(&a, &b, true), distance(&b, &a, true));
        assert!((ab - ba).abs() < 1e-12, "{ab} {ba}");
        assert!(ab > 0.1 && ab < 2f64.sqrt());
    }

    #[test]
    fn disjoint_shapes_are_sqrt_2_apart() {
        let a = blob(300, 40, 60, 80, 10, 30);
        let b = blob(300, 40, 200, 220, 10, 30);
        assert!((distance(&a, &b, false) - 2f64.sqrt()).abs() < 1e-12);
        let (a, b) = (filter(&a, VIEWS[GATE]), filter(&b, VIEWS[GATE]));
        assert!((distance(&a, &b, true) - 2f64.sqrt()).abs() < 1e-12);
    }

    #[test]
    fn a_hand_computed_distance() {
        // a = [1, 1, 0], b = [0, 1, 1]: ||a - b||^2 = 2, ||a||^2 = ||b||^2 = 2, so D = sqrt(2) / sqrt(2) = 1
        let a = Image { w: 3, h: 1, data: vec![1.0, 1.0, 0.0] };
        let b = Image { w: 3, h: 1, data: vec![0.0, 1.0, 1.0] };
        assert!((distance(&a, &b, false) - 1.0).abs() < 1e-12);
        // a = [2, 0], b = [1, 0]: ||a - b|| = 1, norm = sqrt((4 + 1) / 2), D = sqrt(2 / 5)
        let a = Image { w: 2, h: 1, data: vec![2.0, 0.0] };
        let b = Image { w: 2, h: 1, data: vec![1.0, 0.0] };
        assert!((distance(&a, &b, false) - (0.4f64).sqrt()).abs() < 1e-12);
    }

    #[test]
    fn a_shift_of_half_a_pixel_is_forgiven() {
        // b is a moved 4 samples (half a pixel) to the right: the best shift brings it back
        let a = filter(&blob(120, 60, 40, 60, 10, 40), VIEWS[GATE]);
        let b = filter(&blob(120, 60, 44, 64, 10, 40), VIEWS[GATE]);
        assert!(distance(&a, &b, false) > 0.05);
        assert!(distance(&a, &b, true) < 1e-9);
    }

    #[test]
    fn centred_boxes_line_up() {
        let a = blob(9, 3, 4, 5, 1, 2);
        let b = blob(5, 3, 2, 3, 1, 2);
        assert_eq!(pair_distance(&a, &b, Align::Centre), 0.0);
        assert!(pair_distance(&a, &b, Align::Origin) > 1.0);
    }

    #[test]
    fn three_significant_figures() {
        assert_eq!(sig3(540.0), "540");
        assert_eq!(sig3(0.16296), "0.163");
        assert_eq!(sig3(-200.4), "-200");
        assert_eq!(sig3(1.41499), "1.41");
        assert_eq!(sig3(1234.0), "1230");
        assert_eq!(sig3(0.9996), "1.00");
        assert_eq!(sig3(0.0), "0");
    }
}
