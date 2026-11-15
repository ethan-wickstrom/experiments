//! The script capitals of mathematics: 𝒜 to 𝒵, eight of them among the letterlike symbols (ℬ ℰ ℱ ℋ ℐ ℒ ℳ ℛ).
//!
//! They are written, not built: each is one to three strokes of a pen that has 0.92 of the capitals' stem on a
//! downstroke and 0.88 of their hairline on an upstroke and in a hook, leaning six degrees more than the italic
//! ([`LEAN`]; less in the fixed pitch, [`MONO_LEAN`]). The structure is the roman capital's, so that the letter
//! is read as that letter at small sizes. What makes it a script letter is what a hand adds when it writes a
//! capital in one movement, and a reader has to see that at 13 pixels, beside the italic capital that means
//! something else in the same formula (decision T31 has the measurements):
//!
//! - a letter that begins with a downstroke begins in a hook that hangs from the cap height to its left;
//! - a letter that begins with an upstroke begins in a hook that stands on the baseline to its left;
//! - a bowl begins in a flag: a curl left of its stem, from which it runs over the stem's top;
//! - a round letter begins in a hook inside its own top;
//! - a last downstroke ends in a hook to the right on the baseline, a stem that stands alone in one to the
//!   left, and a last upstroke in one that hangs from the cap height to the right;
//! - the bar over a letter hangs from a hook at its left, sags and ends lifted.
//!
//! Every hook is a turn of one radius, [`Hand::r`]: the pen's half breadth and a white that stays open at 13
//! pixels. They lean the same in the upright and the italic faces, as ℓ does.
//!
//! A letter is drawn in a box `w` wide whose left edge is `x0`: a point of it is given in fractions of `w` and
//! of the cap height. In the proportional family the box is the letter's own and the fit measures the ink
//! ([`fit`]); in the fixed pitch every box is what the cell leaves once the lean is taken off.
//!
//! A stroke's level run is written as a straight segment ([`straight`], `line()`), never as a curve between two
//! knots that travel the same way on one line: such a curve has all its points on that line, and where a stem
//! crosses it the union that removes the overlaps of a static font goes wrong.

use rachis_kernel::geom::flatten;
use rachis_kernel::params::SLANT;
use rachis_kernel::pen::{expand, sheared};
use rachis_kernel::{Draw, Fit, Knot, Params, Registry, Spec, knot, pt};

use crate::latin::ink_mid;
use crate::parts::cut_pen;

/// The lean of the script letters in the proportional family, in degrees: six more than the italic's, so that
/// a script capital beside an italic one is seen to lean more.
pub const LEAN: f64 = 16.0;
/// The lean in the fixed pitch: what a letter leans, its cell loses in breadth.
pub const MONO_LEAN: f64 = 8.0;
/// The white the fixed pitch keeps at each side of the box a letter is written in.
const MONO_MARGIN: f64 = 26.0;

// A script capital beside an italic one is seen to lean more, and in the fixed pitch no more than the italic.
const _: () = assert!(LEAN >= SLANT + 5.0 && MONO_LEAN > 0.0 && MONO_LEAN <= SLANT);

fn slope(p: &Params) -> f64 {
    (if p.mono { MONO_LEAN } else { LEAN }).to_radians().tan()
}

/// The box a letter is written in, its two pens and the radius of its hooks.
struct Hand<'a> {
    p: &'a Params,
    x0: f64,
    w: f64,
    /// The breadth of a downstroke.
    s: f64,
    /// The breadth of an upstroke, a bar or a hook.
    h: f64,
    /// The radius of a hook, on the pen's centre line.
    r: f64,
}

impl<'a> Hand<'a> {
    /// A box `natural` wide in the proportional family. In the fixed pitch it is what the cell leaves once the
    /// lean is taken off, the pen is lighter by the power 0.6 of what the box is narrower than the letter's own,
    /// and the white inside a hook is smaller by more than that: a letter written in half its width with its
    /// own pen has no white left in it.
    fn new(p: &'a Params, natural: f64) -> Hand<'a> {
        let own = natural + 1.6 * (p.cap_stem - 94.0);
        let w = if p.mono { p.width - 2.0 * MONO_MARGIN - slope(p) * p.cap } else { own };
        // the sheared box is centred in the cell
        let x0 = (p.width - w) / 2.0 - slope(p) * (p.cap / 2.0 - p.slant_origin());
        let light = (w / own).min(1.0).powf(0.6);
        let h = 0.88 * light * p.cap_hair;
        Hand { p, x0, w, s: 0.92 * light * p.cap_stem, h, r: 0.5 * h + 38.0 * light * light }
    }

    fn x(&self, fx: f64) -> f64 {
        self.x0 + fx * self.w
    }

    fn y(&self, fy: f64) -> f64 {
        fy * self.p.cap
    }

    /// The height, in cap heights, of the centre line of a thin stroke that lies under the cap height.
    fn top(&self) -> f64 {
        1.0 - self.h / (2.0 * self.p.cap)
    }

    /// The same for a round stroke, which overshoots.
    fn top_o(&self) -> f64 {
        self.top() + self.p.over / self.p.cap
    }

    /// The height of the centre line of a thin stroke that lies on the baseline.
    fn base(&self) -> f64 {
        self.h / (2.0 * self.p.cap)
    }

    fn base_o(&self) -> f64 {
        self.base() - self.p.over / self.p.cap
    }

    /// A knot of the downstroke's breadth.
    fn thick(&self, fx: f64, fy: f64) -> Knot {
        knot(self.x(fx), self.y(fy), self.s)
    }

    /// A knot of the upstroke's breadth.
    fn thin(&self, fx: f64, fy: f64) -> Knot {
        knot(self.x(fx), self.y(fy), self.h)
    }

    /// The end of a thin stroke travelling along `dir`: cut along the lean where the stroke runs more level
    /// than steep, and level where it runs steeper. A cut nearly along the stroke would be a spike.
    fn end(&self, fx: f64, fy: f64, dir: f64) -> Knot {
        let steep = dir.to_radians().sin().abs() > std::f64::consts::FRAC_1_SQRT_2;
        cut_pen(self.x(fx), self.y(fy), 0.92 * self.h, dir, if steep { 0.0 } else { 90.0 })
    }

    /// The end of a thick stroke on the cap height or the baseline, cut level.
    fn flat(&self, fx: f64, fy: f64, dir: f64) -> Knot {
        cut_pen(self.x(fx), self.y(fy), self.s, dir, 0.0)
    }

    /// The same for a thin stroke.
    fn flat_thin(&self, fx: f64, fy: f64, dir: f64) -> Knot {
        cut_pen(self.x(fx), self.y(fy), self.h, dir, 0.0)
    }

    /// The direction from one point of the box to another, in degrees.
    fn towards(&self, from: (f64, f64), to: (f64, f64)) -> f64 {
        (self.y(to.1) - self.y(from.1)).atan2(self.x(to.0) - self.x(from.0)).to_degrees()
    }

    /// Knots of the thin pen on the circle of `k` hook radii about (`cx`, `cy`), in font units, from the angle
    /// `from` to the angle `to`: one at each end and one at every quarter turn that is not next to an end. The
    /// pen travels counter-clockwise when `to` is the greater.
    fn arc(&self, cx: f64, cy: f64, k: f64, from: f64, to: f64) -> Vec<Knot> {
        const APART: f64 = 28.0;
        let (r, ccw) = (k * self.r, to > from);
        let quarter = if ccw { 90.0 } else { -90.0 };
        let mut angles = vec![from];
        let mut q = if ccw { (from / 90.0).floor() * 90.0 + 90.0 } else { (from / 90.0).ceil() * 90.0 - 90.0 };
        while if ccw { q < to - APART } else { q > to + APART } {
            if (q - from).abs() > APART {
                angles.push(q);
            }
            q += quarter;
        }
        angles.push(to);
        angles
            .into_iter()
            .map(|a| {
                let (sin, cos) = a.to_radians().sin_cos();
                knot(cx + r * cos, cy + r * sin, self.h).dir(a + quarter)
            })
            .collect()
    }

    /// The knots of a turn of `k` hook radii that begins at (`x`, `y`), in font units, where the pen travels
    /// along `from`, and ends where it travels along `to`: counter-clockwise when `to` is the greater.
    fn turn(&self, x: f64, y: f64, k: f64, from: f64, to: f64) -> Vec<Knot> {
        let side = if to > from { 90.0 } else { -90.0 };
        let (sin, cos) = (from + side).to_radians().sin_cos();
        self.arc(x + k * self.r * cos, y + k * self.r * sin, k, from - side, to - side)
    }

    /// The knots of a turn that ends at (`x`, `y`) travelling along `to`, having begun travelling along `from`.
    fn turn_into(&self, x: f64, y: f64, k: f64, from: f64, to: f64) -> Vec<Knot> {
        let side = if to > from { 90.0 } else { -90.0 };
        let (sin, cos) = (to + side).to_radians().sin_cos();
        self.arc(x + k * self.r * cos, y + k * self.r * sin, k, from - side, to - side)
    }

    /// How far above the lowest point of a turn its end is where the pen travels along `dir`, in hook radii:
    /// `ccw` says which way the turn goes.
    fn rise(dir: f64, ccw: bool) -> f64 {
        1.0 + (dir - if ccw { 90.0 } else { -90.0 }).to_radians().sin()
    }

    /// The height at which a pen travelling along `dir` begins or ends a turn of `k` radii that stands on the
    /// line `fy`.
    fn stands(&self, fy: f64, k: f64, dir: f64, ccw: bool) -> f64 {
        self.y(fy) + self.h / 2.0 + k * self.r * Hand::rise(dir, ccw)
    }

    /// The height at which a pen travelling along `dir` begins or ends a turn of `k` radii that hangs from the
    /// line `fy`.
    fn hangs(&self, fy: f64, k: f64, dir: f64, ccw: bool) -> f64 {
        self.y(fy) - self.h / 2.0 - k * self.r * (2.0 - Hand::rise(dir, ccw))
    }

    /// The hook a letter begins in when it begins with a downstroke at `fx` that travels along `dir`: it hangs
    /// from the cap height to the left. The last knot is the downstroke's first, of its breadth.
    fn entry(&self, fx: f64, dir: f64, k: f64) -> Vec<Knot> {
        let mut ks = self.turn_into(self.x(fx), self.hangs(1.0, k, dir, false), k, dir + 235.0, dir);
        if let Some(last) = ks.last_mut() {
            last.w = self.s;
        }
        ks
    }

    /// The hook a letter begins in when it begins with an upstroke: it stands on the baseline, its centre at
    /// `fx`, and the pen leaves it to the right.
    fn spring(&self, fx: f64) -> Vec<Knot> {
        self.arc(self.x(fx), self.y(0.0) + self.h / 2.0 + self.r, 1.0, 95.0, 285.0)
    }

    /// The end of a downstroke at `fx` that travels along `dir`: a hook to the right that stands on the line
    /// `fy`. The first knot is the downstroke's last, of its breadth.
    fn exit(&self, fx: f64, fy: f64, dir: f64, k: f64) -> Vec<Knot> {
        let mut ks = self.turn(self.x(fx), self.stands(fy, k, dir, true), k, dir, dir + 170.0);
        ks[0].w = self.s;
        ks
    }

    /// The end of a stem at `fx`: a hook to the left that stands on the line `fy`.
    fn foot(&self, fx: f64, fy: f64, k: f64) -> Vec<Knot> {
        let mut ks = self.turn(self.x(fx), self.stands(fy, k, -90.0, false), k, -90.0, -280.0);
        ks[0].w = self.s;
        ks
    }

    /// The end of an upstroke at `fx` that travels along `dir`: a hook to the right that hangs from the cap
    /// height.
    fn flick(&self, fx: f64, dir: f64, k: f64) -> Vec<Knot> {
        self.turn(self.x(fx), self.hangs(1.0, k, dir, false), k, dir, dir - 150.0)
    }

    /// What a bowl begins in: a curl left of the stem at `fx`, from which the pen turns up and runs over the
    /// stem's top.
    fn flag(&self, fx: f64) -> Vec<Knot> {
        let (x, top, r, h) = (self.x(fx), self.y(1.0), self.r, self.h);
        vec![
            knot(x - 1.6 * r, top - 4.3 * r, h).dir(150.0),
            knot(x - 3.0 * r, top - 2.9 * r, h).dir(90.0),
            knot(x - 1.4 * r, top - h / 2.0 - 0.25 * r, h).dir(28.0),
        ]
    }

    /// What a round letter begins in: a hook inside its top right that begins at (`fx`, `fy`), from which the
    /// pen rises to the top of the letter at `over`.
    fn crook(&self, fx: f64, fy: f64, over: f64) -> Vec<Knot> {
        vec![
            self.thin(fx, fy).dir(30.0),
            self.thin(fx + 0.23, fy + 0.16).dir(95.0),
            self.thin(over, self.top_o()).dir(180.0),
        ]
    }
}

/// Add the stroke through `knots`, leaning.
fn write(g: &mut Draw, knots: &[Knot]) {
    let o = g.p.slant_origin();
    let ks: Vec<Knot> = knots.iter().map(|k| sheared(k, slope(g.p), o)).collect();
    match expand(&ks, false) {
        Ok(cs) => cs.into_iter().for_each(|c| g.add_upright(c)),
        Err(e) => g.glyph.errors.push(e),
    }
}

/// Add the closed stroke through `knots`, leaning: a ring.
fn write_ring(g: &mut Draw, knots: &[Knot]) {
    let o = g.p.slant_origin();
    let ks: Vec<Knot> = knots.iter().map(|k| sheared(k, slope(g.p), o)).collect();
    match expand(&ks, true) {
        Ok(cs) => cs.into_iter().for_each(|c| g.add_upright(c)),
        Err(e) => g.glyph.errors.push(e),
    }
}

/// `knots`, of which the segment after the last is straight.
fn straight(mut knots: Vec<Knot>) -> Vec<Knot> {
    if let Some(last) = knots.last_mut() {
        last.line = true;
    }
    knots
}

/// A stem at `fx` between the stroke that runs over it under the cap height and the one that runs under it on
/// the baseline, cut level at both ends. It ends on the centre lines of the two, so that its ends lie inside
/// those strokes and not along their edges.
fn stem(g: &mut Draw, d: &Hand, fx: f64) {
    write(g, &[d.flat(fx, d.top(), -90.0).line(), d.flat(fx, d.base(), -90.0)]);
}

/// A stem at `fx` that begins in a hook at the cap height and is cut level on the baseline.
fn stem_in(g: &mut Draw, d: &Hand, fx: f64) {
    let mut ks = straight(d.entry(fx, -90.0, 1.0));
    ks.push(d.flat(fx, 0.0, -90.0));
    write(g, &ks);
}

/// A stem from the cap height at `fx` that ends in a hook to the right on the baseline: the last stroke of a
/// letter.
fn stem_out(g: &mut Draw, d: &Hand, fx: f64) {
    let mut ks = vec![d.flat(fx, 1.0, -90.0).line()];
    ks.extend(d.exit(fx, 0.0, -90.0, 1.0));
    write(g, &ks);
}

/// A stem from the height `top` at `fx` that ends in a hook to the left on the line `foot`.
fn stem_foot(g: &mut Draw, d: &Hand, fx: f64, top: f64, foot: f64, k: f64) {
    let mut ks = vec![d.flat(fx, top, -90.0).line()];
    ks.extend(d.foot(fx, foot, k));
    write(g, &ks);
}

/// A straight stroke between two points of the box, cut level at both ends.
fn diagonal(g: &mut Draw, d: &Hand, from: (f64, f64), to: (f64, f64), breadth: f64) {
    let dir = d.towards(from, to);
    write(
        g,
        &[
            cut_pen(d.x(from.0), d.y(from.1), breadth, dir, 0.0).line(),
            cut_pen(d.x(to.0), d.y(to.1), breadth, dir, 0.0),
        ],
    );
}

/// The bar over ℱ ℐ 𝒥 𝒯 𝒵: it hangs from a hook of `k` radii at its left, sags and ends lifted.
fn wave(g: &mut Draw, d: &Hand, from: f64, to: f64, k: f64) {
    let top = d.y(d.top());
    let mut ks = d.turn_into(d.x(from) + k * d.r, top, k, 140.0, 0.0);
    let run = to - from;
    ks.extend([d.thin(from + 0.64 * run, d.top() - 0.05).dir(-2.0), d.end(to, d.top() + 0.012, 30.0)]);
    write(g, &ks);
}

/// The stroke ℐ and 𝒵 stand on: the bar again, on the baseline.
fn ground(g: &mut Draw, d: &Hand, from: f64, to: f64) {
    let run = to - from;
    write(
        g,
        &[
            d.end(from, d.base() + 0.15, -70.0),
            d.thin(from + 0.22 * run, d.base()).dir(-4.0),
            d.thin(from + 0.66 * run, d.base() + 0.012).dir(4.0),
            d.end(to, d.base() + 0.17, 54.0),
        ],
    );
}

/// A thin level bar.
fn bar(g: &mut Draw, d: &Hand, from: f64, to: f64, fy: f64) {
    let (y, h) = (d.y(fy), d.h);
    write(g, &[knot(d.x(from), y, h).pen(90.0).line(), knot(d.x(to), y, h).pen(90.0)]);
}

fn cal_a(g: &mut Draw) {
    let d = Hand::new(g.p, 600.0);
    // the left leg rises out of a hook on the baseline
    let mut leg = d.spring(0.13);
    leg.extend([d.thin(0.40, 0.50).dir(66.0), d.flat_thin(0.63, 1.0, 69.0)]);
    write(g, &leg);
    // the right one falls from the apex into a hook
    let mut fall = vec![d.flat(0.65, 1.0, -84.0)];
    fall.extend(d.exit(0.76, 0.0, -90.0, 1.0));
    write(g, &fall);
    bar(g, &d, 0.26, 0.74, 0.34);
}

fn cal_b(g: &mut Draw) {
    let d = Hand::new(g.p, 600.0);
    stem(g, &d, 0.44);
    // the upper bowl, begun in a flag
    let mut upper = d.flag(0.44);
    upper.extend([
        d.thin(0.64, d.top()).dir(0.0),
        d.thick(0.86, 0.78).dir(-90.0),
        d.thin(0.66, 0.60).dir(186.0),
        d.thin(0.44, 0.565).dir(190.0),
    ]);
    write(g, &upper);
    // the lower bowl, which leaves the stem under the upper one's end and runs on under the stem into a hook:
    // the two bowls part at the stem, as the strokes of a 3 do
    let mut lower = vec![
        d.thin(0.44, 0.555).dir(-8.0),
        d.thin(0.70, 0.535).dir(-2.0),
        d.thick(0.99, 0.28).dir(-90.0),
        d.thin(0.68, d.base()).dir(180.0).line(),
    ];
    lower.extend(d.arc(d.x(0.44) - 1.5 * d.r, d.y(d.base()) + d.r, 1.0, -90.0, -235.0));
    write(g, &lower);
}

fn cal_c(g: &mut Draw) {
    let d = Hand::new(g.p, 540.0);
    let mut ks = d.crook(0.60, 0.63, 0.60);
    ks.extend([d.thick(0.085, 0.49).dir(-90.0), d.thin(0.54, d.base_o()).dir(0.0), d.end(0.98, 0.26, 64.0)]);
    write(g, &ks);
}

fn cal_d(g: &mut Draw) {
    let d = Hand::new(g.p, 660.0);
    stem(g, &d, 0.42);
    // one stroke round the stem: out of a hook under its foot, up the bowl and over its top into a curl
    let mut ks = straight(d.arc(d.x(0.42) - 1.5 * d.r, d.y(d.base()) + d.r, 1.0, 125.0, 270.0));
    ks.extend([d.thin(0.60, d.base()).dir(0.0), d.thick(0.975, 0.50).dir(90.0), d.thin(0.62, d.top()).dir(180.0)]);
    let mut flag = d.flag(0.42);
    flag.reverse();
    ks.extend(flag.into_iter().map(|k| Knot { dir: k.dir.map(|a| a + 180.0), ..k }));
    write(g, &ks);
}

fn cal_e(g: &mut Draw) {
    let d = Hand::new(g.p, 500.0);
    // two bowls open to the right, the lower the larger
    write(
        g,
        &[
            d.thin(0.72, 0.74).dir(55.0),
            d.thin(0.86, 0.86).dir(100.0),
            d.thin(0.58, d.top_o()).dir(180.0),
            d.thick(0.22, 0.775).dir(-90.0),
            d.thin(0.46, 0.56).dir(0.0),
            d.thin(0.62, 0.56).dir(0.0),
        ],
    );
    write(
        g,
        &[
            d.thin(0.62, 0.56).dir(180.0),
            d.thin(0.44, 0.56).dir(180.0),
            d.thick(0.06, 0.27).dir(-90.0),
            d.thin(0.52, d.base_o()).dir(0.0),
            d.end(0.98, 0.26, 64.0),
        ],
    );
}

fn cal_f(g: &mut Draw) {
    let d = Hand::new(g.p, 580.0);
    wave(g, &d, 0.08, 1.0, 1.0);
    stem_foot(g, &d, 0.42, 0.93, 0.0, 1.0);
    bar(g, &d, 0.20, 0.80, 0.49);
}

fn cal_g(g: &mut Draw) {
    let d = Hand::new(g.p, 580.0);
    let mut ks = d.crook(0.62, 0.63, 0.60);
    ks.extend([d.thick(0.08, 0.50).dir(-90.0), d.thin(0.47, d.base_o()).dir(0.0), d.thin(0.83, 0.30).dir(84.0)]);
    write(g, &ks);
    // the stem of G goes below the line and hooks left
    stem_foot(g, &d, 0.85, 0.44, -0.27, 1.0);
    bar(g, &d, 0.60, 1.0, 0.44 - d.base());
}

fn cal_h(g: &mut Draw) {
    let d = Hand::new(g.p, 660.0);
    stem_in(g, &d, 0.30);
    stem_out(g, &d, 0.78);
    bar(g, &d, 0.30, 0.78, 0.50);
}

fn cal_i(g: &mut Draw) {
    let d = Hand::new(g.p, 460.0);
    // a bar over it and a stroke under it: 𝒯 has no stroke under it, and 𝒥 goes below the line. The capital I
    // of the fixed pitch has a bar over it and one under it too, and the script letters lean little there: its
    // stem leans by itself, from the right of the bar to the left of the stroke.
    let (top, foot) = if g.p.mono { (0.62, 0.42) } else { (0.52, 0.52) };
    wave(g, &d, 0.06, 0.96, 1.0);
    diagonal(g, &d, (top, 0.93), (foot, 0.03), d.s);
    ground(g, &d, 0.02, 0.98);
}

fn cal_j(g: &mut Draw) {
    let d = Hand::new(g.p, 480.0);
    wave(g, &d, 0.06, 1.0, 1.0);
    stem_foot(g, &d, 0.64, 0.93, -0.27, 1.1);
}

fn cal_k(g: &mut Draw) {
    let d = Hand::new(g.p, 620.0);
    // in the fixed pitch the stem stands further left, behind a smaller hook: the arm and the leg need the room
    let (at, k) = if g.p.mono { (0.22, 0.7) } else { (0.31, 1.0) };
    let mut ks = straight(d.entry(at, -90.0, k));
    ks.push(d.flat(at, 0.0, -90.0));
    write(g, &ks);
    // the arm falls from a hook at the top right to the stem
    write(
        g,
        &[
            d.thin(0.99, 0.78).dir(108.0),
            d.thin(0.87, d.top() - 0.01).dir(188.0),
            d.thin(0.481 + 0.45 * at, 0.76).dir(232.0),
            d.thin(at + 0.05, 0.50).dir(214.0),
        ],
    );
    // and the leg runs out from it into a hook on the baseline
    let mut leg = vec![d.thick(at + 0.12, 0.55).dir(-48.0), d.thick(0.60, 0.27).dir(-62.0)];
    leg.extend(d.exit(0.67, 0.0, -62.0, 1.0));
    write(g, &leg);
}

fn cal_l(g: &mut Draw) {
    let d = Hand::new(g.p, 520.0);
    // one stroke: a hook at the top, the stem, a round corner and the foot, which ends lifted
    write(
        g,
        &[
            d.thin(0.84, 0.74).dir(100.0),
            d.thin(0.64, d.top_o()).dir(180.0),
            d.thick(0.42, 0.72).dir(-94.0),
            d.thick(0.39, 0.30).dir(-90.0),
            d.thin(0.60, d.base()).dir(0.0),
            d.thin(0.82, d.base() + 0.01).dir(4.0),
            d.end(1.02, 0.17, 50.0),
        ],
    );
    // and a loop to the left of the corner, which is what makes it a written L
    let mut tail = straight(d.arc(d.x(0.39) - 1.25 * d.r, d.y(d.base()) + d.r, 1.0, 95.0, 270.0));
    tail.push(d.thin(0.60, d.base()).dir(0.0));
    write(g, &tail);
}

fn cal_m(g: &mut Draw) {
    let d = Hand::new(g.p, 820.0);
    // a thin stem out of a hook, a thick stroke down to the middle, a thin one up, and the last stem
    let mut leg = d.spring(0.10);
    leg.extend([d.thin(0.17, 0.36).dir(84.0), d.flat_thin(0.205, 1.0, 86.0)]);
    write(g, &leg);
    // in the fixed pitch the two strokes meet above the line: at their full length they would leave no white
    let valley = if g.p.mono { 0.34 } else { 0.03 };
    diagonal(g, &d, (0.22, 1.0), (0.49, valley), d.s);
    diagonal(g, &d, (0.49, valley), (0.765, 1.0), d.h);
    let mut fall = vec![d.flat(0.78, 1.0, -88.0)];
    fall.extend(d.exit(0.80, 0.0, -90.0, 1.0));
    write(g, &fall);
}

fn cal_n(g: &mut Draw) {
    let d = Hand::new(g.p, 700.0);
    let mut leg = d.spring(0.12);
    leg.extend([d.thin(0.21, 0.36).dir(84.0), d.flat_thin(0.245, 1.0, 86.0)]);
    write(g, &leg);
    diagonal(g, &d, (0.265, 1.0), (0.76, 0.0), d.s);
    // the last stem rises into a hook, which the cell of the fixed pitch has less room for
    let mut up = vec![d.flat_thin(0.775, 0.0, 89.0).line()];
    up.extend(d.flick(0.78, 89.0, if g.p.mono { 0.75 } else { 1.0 }));
    write(g, &up);
}

/// The ring of 𝒪 and 𝒬: thick at its sides and thin at its top and bottom, and the hook the stroke ends in
/// inside it.
fn ring(g: &mut Draw, d: &Hand) {
    write_ring(
        g,
        &[
            d.thin(0.50, d.top_o()).dir(180.0),
            d.thick(0.075, 0.50).dir(-90.0),
            d.thin(0.50, d.base_o()).dir(0.0),
            d.thick(0.925, 0.50).dir(90.0),
        ],
    );
    write(
        g,
        &[
            d.thin(0.64, d.top_o() - 0.006).dir(190.0),
            d.thin(0.36, 0.76).dir(252.0),
            d.thin(0.44, 0.56).dir(-30.0),
            d.thin(0.58, 0.56).dir(28.0),
        ],
    );
}

fn cal_o(g: &mut Draw) {
    let d = Hand::new(g.p, 600.0);
    ring(g, &d);
}

fn cal_p(g: &mut Draw) {
    let d = Hand::new(g.p, 580.0);
    stem_foot(g, &d, 0.45, 1.0, 0.0, 1.0);
    let mut bowl = d.flag(0.45);
    bowl.extend([
        d.thin(0.68, d.top()).dir(0.0),
        d.thick(0.98, 0.70).dir(-90.0),
        d.thin(0.70, 0.42).dir(180.0),
        d.thin(0.40, 0.44).dir(174.0),
    ]);
    write(g, &bowl);
}

fn cal_q(g: &mut Draw) {
    let d = Hand::new(g.p, 600.0);
    ring(g, &d);
    // the tail is a wave across the foot of the ring
    write(
        g,
        &[
            d.thin(0.34, 0.27).dir(-58.0),
            d.thin(0.54, 0.02).dir(-30.0),
            d.thin(0.82, -0.14).dir(0.0),
            d.end(1.06, -0.04, 50.0),
        ],
    );
}

fn cal_r(g: &mut Draw) {
    let d = Hand::new(g.p, 640.0);
    stem_foot(g, &d, 0.41, 1.0, 0.0, 1.0);
    let mut bowl = d.flag(0.41);
    bowl.extend([
        d.thin(0.62, d.top()).dir(0.0),
        d.thick(0.88, 0.72).dir(-90.0),
        d.thin(0.62, 0.47).dir(180.0),
        d.thin(0.36, 0.49).dir(174.0),
    ]);
    write(g, &bowl);
    let mut leg = vec![d.thick(0.50, 0.47).dir(-42.0), d.thick(0.68, 0.24).dir(-56.0)];
    leg.extend(d.exit(0.76, 0.0, -56.0, 1.0));
    write(g, &leg);
}

fn cal_s(g: &mut Draw) {
    let d = Hand::new(g.p, 520.0);
    let mut ks = d.crook(0.62, 0.66, 0.60);
    ks.extend([
        d.thick(0.20, 0.77).dir(-90.0),
        d.thick(0.52, 0.52).dir(-24.0),
        d.thick(0.86, 0.26).dir(-90.0),
        d.thin(0.48, d.base_o()).dir(180.0),
        d.thin(0.07, 0.19).dir(102.0),
        d.thin(0.22, 0.34).dir(8.0),
        d.thin(0.36, 0.28).dir(-58.0),
    ]);
    write(g, &ks);
}

fn cal_t(g: &mut Draw) {
    let d = Hand::new(g.p, 600.0);
    wave(g, &d, 0.0, 1.0, 1.2);
    stem_foot(g, &d, 0.54, 0.93, 0.0, 1.2);
}

fn cal_u(g: &mut Draw) {
    let d = Hand::new(g.p, 640.0);
    let mut ks = d.entry(0.27, -90.0, 1.0);
    ks.extend([
        d.thick(0.27, 0.36).dir(-90.0),
        d.thin(0.53, d.base_o()).dir(0.0),
        d.thin(0.79, 0.36).dir(90.0).line(),
        d.flat_thin(0.79, 1.0, 90.0),
    ]);
    write(g, &ks);
    stem_out(g, &d, 0.80);
}

fn cal_v(g: &mut Draw) {
    let d = Hand::new(g.p, 600.0);
    // both strokes are bowed: the first falls steeper as it nears the foot, the second leans out as it rises
    let mut ks = d.entry(0.22, -62.0, 1.0);
    ks.push(d.flat(0.50, 0.0, -80.0));
    write(g, &ks);
    // the upstroke ends in a hook that turns back
    let mut up = vec![d.flat_thin(0.515, 0.0, 82.0)];
    up.extend(d.flick(0.80, 58.0, 1.0));
    write(g, &up);
}

fn cal_w(g: &mut Draw) {
    let d = Hand::new(g.p, 860.0);
    let mut ks = d.entry(0.14, -66.0, 1.0);
    ks.push(d.flat(0.335, 0.0, -82.0));
    write(g, &ks);
    // in the fixed pitch the two strokes meet below the cap height, for the same reason as in ℳ
    let peak = if g.p.mono { 0.64 } else { 1.0 };
    diagonal(g, &d, (0.345, 0.0), (0.515, peak), d.h);
    write(g, &[d.flat(0.53, peak, -68.0), d.flat(0.715, 0.0, -82.0)]);
    let mut up = vec![d.flat_thin(0.725, 0.0, 82.0)];
    up.extend(d.flick(0.875, 60.0, 1.0));
    write(g, &up);
}

fn cal_x(g: &mut Draw) {
    let d = Hand::new(g.p, 640.0);
    // the thick stroke falls from a hook at the top left into one at the bottom right, steepest in the middle
    // (four hooks at four corners: in the fixed pitch they are smaller and stand nearer the middle, to stay in
    // the cell)
    let (reach, k) = if g.p.mono { (0.28, 0.7) } else { (0.30, 1.0) };
    let mut ks = d.entry(0.50 - reach, -36.0, k);
    ks.push(d.thick(0.50, 0.50).dir(-60.0));
    ks.extend(d.exit(0.50 + reach, 0.0, -36.0, k));
    write(g, &ks);
    // and the thin one from a hook at the top right into one at the bottom left
    let back = 218.0;
    let mut thin = d.turn_into(d.x(0.53 + reach), d.hangs(1.0, 0.9 * k, back, true), 0.9 * k, back - 150.0, back);
    thin.push(d.thin(0.50, 0.50).dir(238.0));
    thin.extend(d.turn(d.x(0.49 - reach), d.stands(0.0, 0.9 * k, back, false), 0.9 * k, back, back - 150.0));
    write(g, &thin);
}

fn cal_y(g: &mut Draw) {
    let d = Hand::new(g.p, 600.0);
    // the bowl of a u, and a stem that goes below the line
    let mut ks = d.entry(0.24, -90.0, 1.0);
    ks.extend([
        d.thick(0.24, 0.64).dir(-90.0),
        d.thin(0.50, 0.38).dir(0.0),
        d.thin(0.76, 0.64).dir(90.0).line(),
        d.flat_thin(0.76, 1.0, 90.0),
    ]);
    write(g, &ks);
    stem_foot(g, &d, 0.77, 1.0, -0.27, 1.1);
}

fn cal_z(g: &mut Draw) {
    let d = Hand::new(g.p, 600.0);
    wave(g, &d, 0.04, 0.96, 1.15);
    diagonal(g, &d, (0.86, 0.93), (0.16, 0.06), d.s);
    ground(g, &d, 0.04, 1.0);
    bar(g, &d, 0.32, 0.74, 0.50);
}

/// The program of a letter.
pub type Write = fn(&mut Draw);

/// The script capitals in the order of the alphabet, each with the code point it has.
pub const CAPITALS: [(char, Write); 26] = [
    ('𝒜', cal_a),
    ('ℬ', cal_b),
    ('𝒞', cal_c),
    ('𝒟', cal_d),
    ('ℰ', cal_e),
    ('ℱ', cal_f),
    ('𝒢', cal_g),
    ('ℋ', cal_h),
    ('ℐ', cal_i),
    ('𝒥', cal_j),
    ('𝒦', cal_k),
    ('ℒ', cal_l),
    ('ℳ', cal_m),
    ('𝒩', cal_n),
    ('𝒪', cal_o),
    ('𝒫', cal_p),
    ('𝒬', cal_q),
    ('ℛ', cal_r),
    ('𝒮', cal_s),
    ('𝒯', cal_t),
    ('𝒰', cal_u),
    ('𝒱', cal_v),
    ('𝒲', cal_w),
    ('𝒳', cal_x),
    ('𝒴', cal_y),
    ('𝒵', cal_z),
];

/// The height, in cap heights, above which the ink of a script capital may lean past its advance.
const OVERHANG_FROM: f64 = 0.6;

/// The fit of a script capital in the proportional family: the white at its sides. On the left the ink is
/// what its strokes reach. On the right, ink above [`OVERHANG_FROM`] counts for less by what the lean carries
/// it to the right from there: the top of a leaning letter stands past its advance, as an italic letter's
/// does, so that what follows it on the baseline and a subscript stand by its foot and not by its top. The
/// mathematics font states what stands past the advance as the letter's italic correction, which a
/// superscript clears.
pub fn fit(spec: &Spec, p: &Params) -> Option<Fit> {
    let code = *spec.unicodes.first()?;
    let (_, program) = CAPITALS.iter().find(|(c, _)| *c as u32 == code)?;
    let mut g = Draw::new(p, &spec.name, p.width, true);
    program(&mut g);
    let (slope, from) = (slope(p), OVERHANG_FROM * p.cap);
    let (mut left, mut right) = (f64::INFINITY, f64::NEG_INFINITY);
    for contour in &g.glyph.contours {
        for z in contour.segs.iter().flat_map(|seg| flatten(seg, 1.0)) {
            left = left.min(z.x);
            right = right.max(z.x - slope * (z.y - from).max(0.0));
        }
    }
    let white = 0.62 * p.cap_sb;
    left.is_finite().then_some(Fit { width: p.width, left: white - left, right: white - (p.width - right), grown: 1.0 })
}

/// In the fixed pitch, move what was written so that its ink stands in the middle of the cell: a letter that
/// goes below the line leans out of its box to the left there, and one with a curl at its top to the right.
fn centre(g: &mut Draw) {
    let Some((x0, _, x1, _)) = g.glyph.bounds() else { return };
    let by = pt((g.p.width - (x0 + x1)) / 2.0, 0.0);
    for contour in &mut g.glyph.contours {
        *contour = contour.mapped(|z| z + by);
    }
}

/// Where an accent stands over a script capital: over the middle of its ink just under the cap height, which
/// the lean has carried to the right of the middle of its advance.
fn accent(g: &mut Draw) {
    let (cap, hair) = (g.p.cap, g.p.cap_hair);
    if let Some(x) = ink_mid(&g.glyph, cap - 0.5 * hair) {
        g.glyph.anchors.insert("top".into(), pt(x, cap));
    }
}

pub fn register(reg: &mut Registry) {
    reg.module("calligraphic");
    for (c, program) in CAPITALS {
        reg.ch(c, move |g: &mut Draw| {
            program(g);
            if g.p.mono {
                centre(g);
            }
            accent(g);
        });
    }
}

#[cfg(test)]
mod tests {
    use rachis_kernel::params::faces;
    use rachis_kernel::{Glyph, name_of};

    use super::*;

    /// Show every script capital in every master of every face, as the fonts have it.
    fn each(mut see: impl FnMut(char, &Params, &Glyph)) {
        let registry = crate::registry();
        for face in faces() {
            for p in &face.masters {
                for (c, _) in CAPITALS {
                    let g = registry.flat(&name_of(c), p).unwrap_or_else(|| panic!("{c} is not drawn in {}", p.name));
                    assert!(g.errors.is_empty(), "{c} in {}: {:?}", p.name, g.errors);
                    see(c, p, &g);
                }
            }
        }
    }

    #[test]
    fn a_script_capital_stands_between_the_baseline_and_the_cap_height() {
        each(|c, p, g| {
            let (_, y0, _, y1) = g.bounds().expect("ink");
            // a round stroke overshoots, and so does the stroke that runs from a flag over the top of a stem
            assert!(y1 >= p.cap - 1.0 && y1 <= p.cap + 1.2 * p.over, "{c} in {}: its top is at {y1}", p.name);
            if "𝒢𝒥𝒬𝒴".contains(c) {
                assert!(y0 < -0.15 * p.cap && y0 >= p.desc, "{c} in {}: it goes down to {y0}", p.name);
            } else {
                assert!(y0 <= 1.0 && y0 >= -1.2 * p.over, "{c} in {}: its foot is at {y0}", p.name);
            }
        });
    }

    #[test]
    fn in_the_fixed_pitch_a_script_capital_stays_in_its_cell() {
        each(|c, p, g| {
            if !p.mono {
                return;
            }
            let (x0, _, x1, _) = g.bounds().expect("ink");
            assert_eq!(g.advance, p.width, "{c} in {}", p.name);
            assert!(x0 >= 0.0 && x1 <= p.width, "{c} in {}: from {x0} to {x1}", p.name);
            // and in the middle of it
            assert!((x0 - (p.width - x1)).abs() < 1.0, "{c} in {}: from {x0} to {x1}", p.name);
        });
    }

    #[test]
    fn a_script_capital_leans_past_its_advance_by_less_than_the_white_of_the_next() {
        each(|c, p, g| {
            if p.mono {
                return;
            }
            let white = 0.62 * p.cap_sb;
            let (x0, _, x1, _) = g.bounds().expect("ink");
            assert!((x0 - white).abs() < 1.0, "{c} in {}: its ink begins at {x0}", p.name);
            // two script capitals side by side do not touch
            assert!(x1 - g.advance < white, "{c} in {}: {x1} of {}", p.name, g.advance);
            // and nothing below the height from which a letter may overhang stands in the white at its right
            let low = g
                .contours
                .iter()
                .flat_map(|k| k.segs.iter().flat_map(|seg| flatten(seg, 1.0)))
                .filter(|z| z.y <= OVERHANG_FROM * p.cap)
                .fold(f64::NEG_INFINITY, |x, z| x.max(z.x));
            assert!(low <= g.advance - white + 1.0, "{c} in {}: {low} of {}", p.name, g.advance);
        });
    }

    #[test]
    fn an_accent_stands_over_the_ink_a_script_capital_has_under_the_cap_height() {
        each(|c, p, g| {
            let top = g.anchors.get("top").unwrap_or_else(|| panic!("{c} in {} has no place for an accent", p.name));
            let (x0, _, x1, _) = g.bounds().expect("ink");
            assert_eq!(top.y, p.cap);
            assert!(top.x > x0 && top.x < x1, "{c} in {}: {} outside {x0} to {x1}", p.name, top.x);
        });
    }

    #[test]
    fn every_script_capital_of_unicode_is_written_once() {
        let codes: Vec<u32> = CAPITALS.iter().map(|(c, _)| *c as u32).collect();
        let mut sorted = codes.clone();
        sorted.sort_unstable();
        sorted.dedup();
        assert_eq!(sorted.len(), 26);
        // the block's holes are the letters that the Letterlike Symbols had already
        for (i, code) in codes.iter().enumerate() {
            let in_block = 0x1D49C + i as u32;
            assert!(*code == in_block || (0x2100..0x2150).contains(code), "letter {i} is U+{code:04X}");
        }
    }
}
