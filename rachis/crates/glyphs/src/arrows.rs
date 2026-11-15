//! Arrows.
//!
//! The group is a system, like the operators it stands beside. Every arrow is drawn in a frame of its own (a
//! [`Frame`]: the arrow points along +x, its shaft on y = 0, its middle at x = 0) and the frame is then put in
//! the cell: on the axis, turned to the arrow's heading, reflected if need be. So ↑ is → turned, ↙ is → turned
//! 225 degrees, ↩ is ↪ reflected, and they share every measurement.
//!
//! A straight arrow is an [`Arrow`]: two ends (a head, a barb, a bar, a tail, a hook, ...), one to four shafts
//! (rails), a kind of line (solid, dashed, wave, zigzag) and a mark across it (the slash of ≠, strokes, a ring);
//! [`draw`] assembles it from the primitives. The arrows that are not straight (corner, circular and block
//! arrows) are built from the same head, stroke and frame.
//!
//! The head is the chevron of `>` (operators.rs): as tall as `>`, with its stroke, its flat tip and its plumb end
//! cuts, but shorter. At the angle of `>`, a head short enough to leave room for a shaft closes up into a
//! triangle (its notch is smaller than its end cut), so the head is steeper than `>`: about 40 degrees from the
//! shaft. The shaft is `p.op` thick, on the axis, across the operators' span, and ends inside the head, past
//! the notch and short of the tip. So `->` and `→`, `=>` and `⇒` have one height and one weight.

use rachis_kernel::{Draw, Fit, Knot, Opt, Params, Registry, V, knot, name_of, pt};

use crate::operators::{
    chevron, chevron_rise, circle, equal_pitch, fine, half_span, inset, rel_gap, small_ring, strike, tip, triple_pitch,
    wave_rise,
};
use crate::parts::cut;

// ---------------------------------------------------------------------------------------------------------------
// The frame

/// Where an arrow drawn in its own coordinates goes in the cell: `o` is the image of its middle, `u` of its
/// direction (+x), `v` of its left (+y).
#[derive(Clone, Copy, Debug)]
pub struct Frame {
    o: V,
    u: V,
    v: V,
}

impl Frame {
    /// The arrow centred on the axis in the middle of the cell, pointing along `heading` (degrees, 0 is right).
    pub fn new(p: &Params, heading: f64) -> Frame {
        Frame { o: pt(p.mid(), p.axis), u: V::unit(heading), v: V::unit(heading + 90.0) }
    }

    /// Reflected in the arrow's line: what was on its left is on its right.
    pub fn flipped(self) -> Frame {
        Frame { v: -self.v, ..self }
    }

    /// Reflected across the arrow's middle: the near end becomes the far one.
    pub fn back(self) -> Frame {
        Frame { u: -self.u, ..self }
    }

    /// Moved to the point (x, y) of this frame.
    pub fn at(self, x: f64, y: f64) -> Frame {
        Frame { o: self.z(pt(x, y)), ..self }
    }

    /// A frame whose middle is the point `c` of this one and whose arrow points along `heading` in it.
    pub fn turned(self, c: V, heading: f64) -> Frame {
        let (a, b) = (V::unit(heading), V::unit(heading + 90.0));
        Frame { o: self.z(c), u: self.u * a.x + self.v * a.y, v: self.u * b.x + self.v * b.y }
    }

    pub fn z(self, z: V) -> V {
        self.o + self.u * z.x + self.v * z.y
    }

    fn angle(self, degrees: f64) -> f64 {
        let d = V::unit(degrees);
        let w = self.u * d.x + self.v * d.y;
        w.y.atan2(w.x).to_degrees()
    }

    pub fn knots(self, knots: &[Knot]) -> Vec<Knot> {
        knots
            .iter()
            .map(|k| Knot {
                z: self.z(k.z),
                dir: k.dir.map(|d| self.angle(d)),
                pen: k.pen.map(|a| self.angle(a)),
                ..*k
            })
            .collect()
    }

    pub fn poly(self, g: &mut Draw, points: &[V]) {
        let pts: Vec<V> = points.iter().map(|&z| self.z(z)).collect();
        g.poly(&pts);
    }

    pub fn stroke(self, g: &mut Draw, knots: &[Knot]) {
        g.stroke(&self.knots(knots));
    }

    /// The outline of a polygon, `t` thick, inside it, with mitred corners.
    pub fn outline(self, g: &mut Draw, points: &[V], t: f64) {
        let mut pts: Vec<V> = points.iter().map(|&z| self.z(z)).collect();
        if area(&pts) < 0.0 {
            pts.reverse();
        }
        let knots: Vec<Knot> = inset(&pts, t / 2.0).into_iter().map(|z| Knot::at(z, t).line()).collect();
        g.stroke_closed(&knots);
    }

    /// A rectangle from x0 to x1 and y0 to y1 of this frame.
    pub fn rect(self, g: &mut Draw, x0: f64, y0: f64, x1: f64, y1: f64) {
        self.poly(g, &[pt(x0, y0), pt(x1, y0), pt(x1, y1), pt(x0, y1)]);
    }
}

fn area(points: &[V]) -> f64 {
    let n = points.len();
    (0..n).map(|i| points[i].cross(points[(i + 1) % n])).sum::<f64>() / 2.0
}

// ---------------------------------------------------------------------------------------------------------------
// Measurements

/// Half the length of an arrow: the operators' span.
pub fn reach(p: &Params) -> f64 {
    half_span(p)
}

/// Half the length of an arrow with a head at each end: it takes most of the operators' margins, so that the
/// shaft shows between the heads.
pub fn reach_both(p: &Params) -> f64 {
    p.mid() - 0.3 * p.op_l
}

/// How much shorter the heads of an arrow with a head at each end are (their height stays): those of an arrow
/// of one shaft and of several.
pub const BOTH_HEADS: (f64, f64) = (0.85, 0.65);

/// Half the length of a long arrow ⟶: from edge to edge of the cell in the fixed-pitch family, so that it joins
/// a dash; within the operators' margins in the wider cell the proportional family gives it.
pub fn reach_long(p: &Params) -> f64 {
    if p.mono { p.mid() } else { p.mid() - p.op_l }
}

/// An arrowhead pointing along +x: its length from the open ends to the tip, how far its outer corners are from
/// the shaft, its stroke and the flat of its tip.
#[derive(Clone, Copy, Debug)]
pub struct Head {
    pub len: f64,
    pub rise: f64,
    pub t: f64,
    pub flat: f64,
}

impl Head {
    fn slope(&self) -> f64 {
        (self.rise - self.flat / 2.0) / self.len
    }

    /// The height of an arm's plumb end cut.
    fn cut(&self) -> f64 {
        self.t * self.len.hypot(self.rise - self.flat / 2.0) / self.len
    }

    /// Where the inner edges of the arms meet, for a head whose tip is at `xt`.
    fn crotch(&self, xt: f64) -> f64 {
        xt - self.len + (self.rise - self.cut()) / self.slope()
    }

    fn inner(&self, xt: f64, y: f64) -> f64 {
        self.crotch(xt) - y.abs() / self.slope()
    }

    fn outer(&self, xt: f64, y: f64) -> f64 {
        xt - (y.abs() - self.flat / 2.0) / self.slope()
    }

    /// The centre line of an arm at the height `y`: where a shaft that runs into the arm ends.
    fn centre(&self, xt: f64, y: f64) -> f64 {
        (self.inner(xt, y) + self.outer(xt, y)) / 2.0
    }

    /// Where a shaft `ts` thick on the axis ends: past the notch, so that no white is left between it and the
    /// arms, and short of the tip, so that the tip stays sharp.
    fn shaft_end(&self, xt: f64, ts: f64) -> f64 {
        let c = self.crotch(xt);
        c + 0.5 * (self.outer(xt, ts / 2.0) - c)
    }

    fn poly(&self, xt: f64) -> Vec<V> {
        chevron(xt, xt - self.len, 0.0, self.rise, self.t, self.flat)
    }

    /// The arm of the head on the +y side, ending at the tip in a point over the shaft `ts` thick: the head of
    /// a harpoon. Returns the polygon and where the shaft ends.
    fn barb(&self, xt: f64, ts: f64) -> (Vec<V>, f64) {
        let xo = xt - self.len;
        let b = self.outer(xt, ts / 2.0);
        let q = self.inner(xt, ts / 2.0);
        let pts = vec![
            pt(xo, self.rise),
            pt(xt, self.flat / 2.0),
            pt(xt, -self.flat / 2.0),
            pt(b, -ts / 2.0),
            pt(q, -ts / 2.0),
            pt(q, ts / 2.0),
            pt(xo, self.rise - self.cut()),
        ];
        (pts, (q + b) / 2.0)
    }
}

/// The head of the arrows: as tall as `>`, steeper, a little longer in the Bold so that its notch stays open.
pub fn head(p: &Params) -> Head {
    Head { len: 150.0 + 0.75 * p.op, rise: chevron_rise(p), t: p.op, flat: tip(p) }
}

/// The distance between the centre lines of the shafts of an arrow of `n` shafts: those of = for two, of ≡ for
/// three, closer for four.
pub fn rail_pitch(p: &Params, n: usize) -> f64 {
    match n {
        0 | 1 => 0.0,
        2 => equal_pitch(p),
        3 => triple_pitch(p),
        _ => 0.78 * triple_pitch(p),
    }
}

/// The head of an arrow of `n` shafts: taller by part of the shafts' spread, so that the outer shafts run into
/// its arms, and a little longer.
pub fn head_for(p: &Params, n: usize) -> Head {
    let h = head(p);
    let spread = (n as f64 - 1.0) / 2.0 * rail_pitch(p, n);
    Head { rise: h.rise + 0.45 * spread, len: h.len + 0.3 * spread, ..h }
}

/// The stroke between the operators' and the fine one: for marks across a shaft, the outline of the white
/// arrows and the circular arrows.
pub fn mid_stroke(p: &Params) -> f64 {
    0.5 * (p.op + fine(p))
}

/// A small head drawn with the stroke `t`: for the arrows set in pairs, the circular arrows and the arrows over
/// letters. Its notch stays open because its stroke is lighter, not because it is large.
pub fn small_head(p: &Params, t: f64) -> Head {
    let rise = 50.0 + 1.1 * t;
    Head { len: 1.6 * rise, rise, t, flat: 0.8 * tip(p) }
}

/// The stroke of the small arrows set in pairs (⇄ ⇉): lighter than the fine stroke, so that two heads fit in
/// the cell side by side and keep their notches.
pub fn pair_stroke(p: &Params) -> f64 {
    0.85 * fine(p)
}

/// The distance between the centre lines of a pair of arrows: their heads clear each other by the white
/// between a relation and its bar.
pub fn pair_pitch(p: &Params) -> f64 {
    2.0 * small_head(p, pair_stroke(p)).rise + 0.55 * rel_gap(p)
}

/// The outer radius and the stroke of the ring on a shaft (⇴): smaller than ∘, so that it fits the free stretch
/// of the Bold's shaft, and lighter, so that it stays open.
pub fn ring_mark(p: &Params) -> (f64, f64) {
    (0.8 * small_ring(p), 0.8 * fine(p))
}

/// The white between a head and the bar it points at (⇥).
pub fn stop_gap(p: &Params) -> f64 {
    0.55 * rel_gap(p)
}

/// The white inside a hook (↪), between its arm and the shaft.
pub fn hook_counter(p: &Params) -> f64 {
    90.0 + 0.25 * p.op
}

// ---------------------------------------------------------------------------------------------------------------
// The straight arrow

/// What is at one end of an arrow.
#[derive(Clone, Copy, Debug, PartialEq)]
pub enum End {
    /// The shaft just ends.
    Plain,
    /// An arrowhead pointing out.
    Head,
    /// Two arrowheads, one behind the other (↠).
    Two,
    /// One arm of a head, on the arrow's left (⇀).
    Barb,
    /// A bar across the end (the tail of ↦).
    Bar,
    /// A head pointing at a bar (⇥).
    ToBar,
    /// A chevron pointing the arrow's way, its tip on the shaft (the tail of ↣).
    Feather,
    /// A hook on the arrow's left (the tail of ↪).
    Hook,
    /// A head outlined as a triangle (⇾).
    Open,
}

impl End {
    fn pointed(self) -> bool {
        matches!(self, End::Head | End::Two | End::Barb | End::ToBar | End::Open)
    }
}

#[derive(Clone, Copy, Debug, PartialEq)]
pub enum Line {
    Solid,
    Dashed,
    Wave,
    Zigzag,
}

#[derive(Clone, Copy, Debug, PartialEq)]
pub enum Mark {
    None,
    /// The slash of ≠ across the shafts.
    Slash,
    /// So many strokes across the shaft, square to it.
    Strokes(usize),
    /// A small ring on the shaft.
    Ring,
}

#[derive(Clone, Copy, Debug)]
pub struct Arrow {
    pub tail: End,
    pub tip: End,
    pub rails: usize,
    pub line: Line,
    pub mark: Mark,
    /// Half the length.
    pub l: f64,
    pub h: Head,
    pub t: f64,
}

impl Arrow {
    /// The plain arrow → of this master.
    pub fn new(p: &Params) -> Arrow {
        Arrow {
            tail: End::Plain,
            tip: End::Head,
            rails: 1,
            line: Line::Solid,
            mark: Mark::None,
            l: reach(p),
            h: head(p),
            t: p.op,
        }
    }

    /// The same arrow with other ends. One with a point at each end is longer (see [`reach_both`]).
    pub fn ends(self, tail: End, tip: End, p: &Params) -> Arrow {
        if tail.pointed() && tip.pointed() {
            let k = if self.rails > 1 { BOTH_HEADS.1 } else { BOTH_HEADS.0 };
            let h = Head { len: k * self.h.len, ..self.h };
            return Arrow { tail, tip, l: self.l + reach_both(p) - reach(p), h, ..self };
        }
        Arrow { tail, tip, ..self }
    }

    pub fn rails(self, n: usize, p: &Params) -> Arrow {
        Arrow { rails: n, h: head_for(p, n), ..self }
    }

    pub fn small(self, p: &Params) -> Arrow {
        Arrow { h: small_head(p, pair_stroke(p)), t: pair_stroke(p), ..self }
    }
}

/// Where a shaft ends at one end: at a plumb cut, or (for the outer shafts of an arrow of several) along the
/// centre line of the arm of a head whose tip is at `xt`, the middle shaft at a plumb cut. In the coordinates
/// of that end's frame.
#[derive(Clone, Copy, Debug)]
enum Cut {
    At(f64),
    Arm(Head, f64, f64),
}

impl Cut {
    fn x(self, y: f64) -> f64 {
        match self {
            Cut::At(x) => x,
            Cut::Arm(h, xt, x_axis) => {
                if y.abs() < 1.0 {
                    x_axis
                } else {
                    h.centre(xt, y)
                }
            }
        }
    }

    /// The same for a shaft whose edges are at `a` and `b`: a shaft that straddles the axis ends plumb.
    fn edges(self, a: f64, b: f64) -> (f64, f64) {
        match self {
            Cut::Arm(_, _, x) if a < 0.0 && b > 0.0 => (x, x),
            _ => (self.x(a), self.x(b)),
        }
    }
}

/// Draw one end of the arrow `a` in the frame `f` of that end (the end at +`a.l`, the shaft towards -x).
/// Returns how the shaft ends there and where the end's own shapes begin: the free shaft lies short of it.
fn end(g: &mut Draw, f: Frame, a: &Arrow, kind: End) -> (Cut, f64) {
    let p = g.p;
    let (l, h, t) = (a.l, a.h, a.t);
    let headed = |g: &mut Draw, xt: f64| -> (Cut, f64) {
        f.poly(g, &h.poly(xt));
        let xa = h.shaft_end(xt, t);
        if a.rails > 1 { (Cut::Arm(h, xt, xa), xt - h.len) } else { (Cut::At(xa), xt - h.len) }
    };
    match kind {
        End::Plain => (Cut::At(l), l),
        End::Head => headed(g, l),
        End::Two => {
            f.poly(g, &h.poly(l));
            headed(g, l - 0.6 * h.len)
        }
        End::ToBar => {
            f.rect(g, l - t, -h.rise, l, h.rise);
            headed(g, l - t - stop_gap(p))
        }
        End::Bar => {
            f.rect(g, l - t, -h.rise, l, h.rise);
            (Cut::At(l - t / 2.0), l - t)
        }
        End::Barb => {
            let (pts, xa) = h.barb(l, t);
            f.poly(g, &pts);
            (Cut::At(xa), l - h.len)
        }
        End::Feather => {
            // a chevron pointing back along the shaft in this frame, its open ends at the end of the arrow
            let fh = Head { len: 0.72 * h.len, ..h };
            let xt = l - fh.len;
            f.back().poly(g, &fh.poly(-xt));
            (Cut::At(xt + fh.flat), xt)
        }
        End::Hook => {
            let top = t + hook_counter(p); // the centre line of the hook's arm
            let r = top / 2.0;
            let xa = l - t / 2.0 - r;
            f.stroke(
                g,
                &[
                    knot(xa - 0.45 * r, top, t).pen(90.0).line(),
                    knot(xa, top, t).pen(90.0).dir(0.0).k(p.sq),
                    knot(l - t / 2.0, r, t).dir(-90.0).k(p.sq),
                    knot(xa, 0.0, t).pen(90.0).dir(180.0).line(),
                    knot(xa - 0.5 * r, 0.0, t).pen(90.0),
                ],
            );
            (Cut::At(xa - 0.25 * r), xa - 0.45 * r)
        }
        End::Open => {
            // longer than the head and drawn with a lighter stroke, so that the triangle stays open
            let to = 0.8 * fine(p);
            let xo = l - 1.35 * h.len;
            f.outline(g, &[pt(l, 0.0), pt(xo, h.rise), pt(xo, -h.rise)], to);
            (Cut::At(xo + to / 2.0), xo)
        }
    }
}

/// A plumb-cut shaft from `x0` to `x1` at the height `y`.
fn shaft(g: &mut Draw, f: Frame, x0: f64, x1: f64, y: f64, t: f64) {
    f.rect(g, x0, y - t / 2.0, x1, y + t / 2.0);
}

/// Draw the arrow `a` in the frame `f`.
pub fn draw(g: &mut Draw, f: Frame, a: &Arrow) {
    let p = g.p;
    let t = a.t;
    let (c1, v1) = end(g, f, a, a.tip);
    let (c0, v0) = end(g, f.back(), a, a.tail);
    // the free stretch of the shaft lies between -v0 and v1; its middle carries the mark
    let (fa, fb) = (-v0, v1);
    let xc = (fa + fb) / 2.0;
    let (x0, x1) = (-c0.x(0.0), c1.x(0.0));
    match a.line {
        Line::Solid => {
            let pitch = rail_pitch(p, a.rails);
            for i in 0..a.rails {
                let y = (i as f64 - (a.rails as f64 - 1.0) / 2.0) * pitch;
                let (lo, hi) = (y - t / 2.0, y + t / 2.0);
                let (s0, s1) = c0.edges(lo, hi);
                let (e0, e1) = c1.edges(lo, hi);
                if a.mark == Mark::Ring {
                    let (r, tr) = ring_mark(p);
                    shaft(g, f, x0, xc - r + tr / 2.0, y, t);
                    shaft(g, f, xc + r - tr / 2.0, x1, y, t);
                } else {
                    f.poly(g, &[pt(-s0, lo), pt(e0, lo), pt(e1, hi), pt(-s1, hi)]);
                }
            }
        }
        Line::Dashed => {
            // two dashes and two gaps on the free stretch, then the shaft into the head; a gap is 0.7 of a
            // dash, and a dash is no shorter than the stroke is thick in the Bold
            let d = (fb - x0) / (2.0 * 1.7);
            for i in 0..2 {
                let s = x0 + i as f64 * 1.7 * d;
                shaft(g, f, s, s + d, 0.0, t);
            }
            shaft(g, f, fb, x1, 0.0, t);
        }
        Line::Wave => {
            // the wave of the tilde, one period on the free stretch, level where it runs into a head
            let w = fb - fa;
            let amp = 0.85 * wave_rise(p);
            let start =
                if a.tail.pointed() { knot(x0, 0.0, t).pen(90.0).dir(0.0) } else { cut(x0, -0.5 * amp, t, 40.0) };
            f.stroke(
                g,
                &[
                    start,
                    knot(fa + 0.25 * w, amp, t).dir(0.0),
                    knot(fa + 0.66 * w, -amp, t).dir(0.0),
                    knot(fb, 0.0, t).pen(90.0).dir(0.0).line(),
                    knot(x1, 0.0, t).pen(90.0),
                ],
            );
        }
        Line::Zigzag => {
            // three straight strokes up and down at about 50 degrees, then the shaft into the head
            let w = fb - x0;
            let amp = 0.55 * wave_rise(p);
            let n = 3;
            let step = w / n as f64;
            let mut ks = vec![knot(x0, 0.0, t).pen(90.0).line()];
            for i in 0..n {
                let x = x0 + (i as f64 + 0.5) * step;
                ks.push(Knot::at(pt(x, if i % 2 == 0 { amp } else { -amp }), t).line());
            }
            ks.push(Knot::at(pt(fb, 0.0), t).line());
            ks.push(knot(x1, 0.0, t).pen(90.0));
            f.stroke(g, &ks);
        }
    }
    match a.mark {
        Mark::None => {}
        Mark::Slash => {
            // the slash of ≠, with its stroke and its cut, as tall as the head (past the outer shafts by a
            // stroke) and leaning less, so that it stays clear of the head: the one of ≠ would cross it
            let spread = (a.rails as f64 - 1.0) / 2.0 * rail_pitch(p, a.rails);
            let dy = if a.rails > 1 { spread + a.t } else { a.h.rise };
            let x = if a.tail.pointed() { xc } else { xc - 0.12 * dy }; // away from the head it leans towards
            let c = f.z(pt(x, 0.0));
            strike(g, c.x, c.y, 0.32 * dy, dy, None);
        }
        Mark::Strokes(n) => {
            let ts = fine(p);
            let bh = 0.6 * a.h.rise;
            let pitch = ts + 0.5 * rel_gap(p);
            for i in 0..n {
                let x = xc + (i as f64 - (n as f64 - 1.0) / 2.0) * pitch;
                f.rect(g, x - ts / 2.0, -bh, x + ts / 2.0, bh);
            }
        }
        Mark::Ring => {
            let c = f.z(pt(xc, 0.0));
            let (r, tr) = ring_mark(p);
            circle(g, c.x, c.y, r, None, Some(tr));
        }
    }
}

// ---------------------------------------------------------------------------------------------------------------
// Arrows that turn

/// A corner arrow in its frame: a stem at x = `xs` that comes down from y = `h` to the shaft, turns a round
/// corner and runs along y = 0 to a head at `l`. ↳ is this; ↲ ↰ ↱ ↴ ↵ are its reflections and turns.
fn corner(g: &mut Draw, f: Frame, xs: f64, h: f64, l: f64) {
    let p = g.p;
    let t = p.op;
    let hd = head(p);
    f.poly(g, &hd.poly(l));
    let r = 1.2 * t;
    f.stroke(
        g,
        &[
            knot(xs, h, t).pen(0.0).line(),
            knot(xs, r, t).pen(0.0).dir(-90.0).k(p.sq),
            knot(xs + r, 0.0, t).pen(90.0).dir(0.0).line(),
            knot(hd.shaft_end(l, t), 0.0, t).pen(90.0),
        ],
    );
}

/// Put a corner arrow whose stem is at `xs` and `h` tall in the middle of the cell, and draw it.
fn corner_centred(g: &mut Draw, f: Frame, xs: f64, h: f64) {
    let p = g.p;
    let l = reach(p);
    let rise = head(p).rise;
    let dx = -(l + xs - p.op / 2.0) / 2.0;
    let dy = -(h - rise) / 2.0;
    corner(g, f.at(dx, dy), xs + 0.0, h, l);
}

/// ↳ and its kin: the stem as long as the arrow, the shaft shorter.
fn corner_tall(g: &mut Draw, f: Frame) {
    let p = g.p;
    let l = reach(p);
    corner_centred(g, f, -0.62 * l, 2.0 * l - head(p).rise);
}

/// ↵: a long shaft and a short stem.
fn corner_return(g: &mut Draw, f: Frame) {
    let p = g.p;
    let l = reach(p);
    corner_centred(g, f, -1.12 * l, 1.05 * head(p).rise + 0.5 * l);
}

/// A circular arrow: an arc of radius `rc` (centre line) about `c`, from the angle `a0` to `a1` (degrees;
/// anticlockwise when a1 > a0), stroked `t`, which runs on straight along its tangent into a head `h`.
fn circular(g: &mut Draw, c: V, rc: f64, a0: f64, a1: f64, h: &Head, t: f64) {
    let s = if a1 > a0 { 1.0 } else { -1.0 };
    let tangent = a1 + s * 90.0;
    let z1 = c + V::unit(a1) * rc;
    // the head's open ends are where the arc ends
    let hf = Frame { o: z1 + V::unit(tangent) * h.len, u: V::unit(tangent), v: V::unit(tangent + 90.0) };
    hf.poly(g, &h.poly(0.0));
    let n = ((a1 - a0).abs() / 90.0).ceil() as usize;
    let mut ks = Vec::new();
    for i in 0..=n {
        let a = a0 + (a1 - a0) * i as f64 / n as f64;
        ks.push(Knot::at(c + V::unit(a) * rc, t).dir(a + s * 90.0));
    }
    ks[0] = ks[0].pen(a0);
    ks[n] = ks[n].line();
    ks.push(Knot::at(hf.z(pt(h.shaft_end(0.0, t), 0.0)), t).pen(a1));
    g.stroke(&ks);
}

/// The head and stroke of the circular arrows.
fn turning(p: &Params) -> (Head, f64) {
    let t = mid_stroke(p);
    (small_head(p, t), t)
}

/// ↶ ↷: half a circle over the top, the head at its end pointing down.
fn semicircle(g: &mut Draw, clockwise: bool) {
    let p = g.p;
    let (h, t) = turning(p);
    let half = p.mid() - 0.5 * p.op_l; // half the width it may take
    let rc = (2.0 * half - h.rise - t / 2.0) / 2.0;
    let s = if clockwise { -1.0 } else { 1.0 };
    let cx = p.mid() + s * (h.rise - t / 2.0) / 2.0;
    let cy = p.axis - (rc + t / 2.0 - h.len) / 2.0;
    let (a0, a1) = if clockwise { (180.0, 0.0) } else { (0.0, 180.0) };
    circular(g, pt(cx, cy), rc, a0, a1, &h, t);
}

/// ↺ ↻: most of a circle, its head on the top pointing along it, the gap under the head.
fn open_circle(g: &mut Draw, clockwise: bool) {
    let p = g.p;
    let (h, t) = turning(p);
    let rc = reach(p) - t / 2.0 - 0.05 * h.rise;
    let c = pt(p.mid(), p.axis - (h.rise - t / 2.0) / 2.0);
    if clockwise {
        circular(g, c, rc, 20.0, -270.0, &h, t);
    } else {
        circular(g, c, rc, 160.0, 450.0, &h, t);
    }
}

// ---------------------------------------------------------------------------------------------------------------
// Block arrows: white (outlined) and black (filled)

/// The outline of a block arrow in its frame, from its tail at `x0` to its tip at `x1`: a shaft `w` to each side
/// of the axis and a triangular head `r` to each side, its sides at 45 degrees.
fn block(x0: f64, x1: f64, r: f64, w: f64) -> Vec<V> {
    let xo = x1 - r;
    vec![pt(x0, -w), pt(xo, -w), pt(xo, -r), pt(x1, 0.0), pt(xo, r), pt(xo, w), pt(x0, w)]
}

/// The same with a head at each end.
fn block_both(x0: f64, x1: f64, r: f64, w: f64) -> Vec<V> {
    let (xa, xb) = (x0 + r, x1 - r);
    vec![
        pt(x0, 0.0),
        pt(xa, -r),
        pt(xa, -w),
        pt(xb, -w),
        pt(xb, -r),
        pt(x1, 0.0),
        pt(xb, r),
        pt(xb, w),
        pt(xa, w),
        pt(xa, r),
    ]
}

/// The head and shaft half-widths of the white arrows (⇧ ⇨) and the stroke of their outline: lighter than the
/// fine stroke, so that the shaft keeps a counter in the Bold.
fn white(p: &Params) -> (f64, f64, f64) {
    let l = reach(p);
    (0.88 * l, 0.45 * l, 0.85 * fine(p))
}

/// The head and shaft half-widths of the black arrows (⬆ ➡): a shaft about two strokes thick.
fn black(p: &Params) -> (f64, f64) {
    let w = 0.95 * p.op + 6.0;
    (w + 0.42 * reach(p), w)
}

fn white_arrow(g: &mut Draw, f: Frame) {
    let p = g.p;
    let l = reach(p);
    let (r, w, t) = white(p);
    f.outline(g, &block(-l, l, r, w), t);
}

fn white_arrow_both(g: &mut Draw, f: Frame) {
    let p = g.p;
    let l = reach_both(p);
    let (r, w, t) = white(p);
    f.outline(g, &block_both(-l, l, 0.9 * r, w), t);
}

#[derive(Clone, Copy, Debug, PartialEq)]
enum Base {
    Box,
    Pedestal,
    PedestalBar,
    PedestalStem,
    Wall,
}

/// ⇪ and its kin: the white arrow shortened, over a box, a pedestal or a wall.
fn white_arrow_over(g: &mut Draw, f: Frame, base: Base) {
    let p = g.p;
    let l = reach(p);
    let (r, w, t) = white(p);
    let r = 0.9 * r;
    let foot = 0.30 * l; // how long what is under the arrow is
    let gap = 0.5 * rel_gap(p);
    let xo = l - r;
    match base {
        Base::Box => {
            f.outline(g, &block(-l + foot + gap, l, r, w), t);
            f.outline(g, &[pt(-l, -w), pt(-l + foot, -w), pt(-l + foot, w), pt(-l, w)], t);
        }
        Base::Pedestal | Base::PedestalBar | Base::PedestalStem => {
            // the shaft widens into a pedestal
            let x = -l + foot;
            let wp = 0.82 * r;
            f.outline(
                g,
                &[
                    pt(-l, -wp),
                    pt(x, -wp),
                    pt(x, -w),
                    pt(xo, -w),
                    pt(xo, -r),
                    pt(l, 0.0),
                    pt(xo, r),
                    pt(xo, w),
                    pt(x, w),
                    pt(x, wp),
                    pt(-l, wp),
                ],
                t,
            );
            if base == Base::PedestalBar {
                let xb = (x + xo) / 2.0;
                f.rect(g, xb - t / 2.0, -w, xb + t / 2.0, w);
            }
            if base == Base::PedestalStem {
                f.rect(g, -l, -t / 2.0, xo, t / 2.0);
            }
        }
        Base::Wall => {
            f.outline(g, &block(-l + t + gap, l, r, w), t);
            f.rect(g, -l, -r, -l + t, r);
        }
    }
}

fn black_arrow(g: &mut Draw, f: Frame) {
    let p = g.p;
    let l = reach(p);
    let (r, w) = black(p);
    f.poly(g, &block(-l, l, r, w));
}

fn black_arrow_both(g: &mut Draw, f: Frame) {
    let p = g.p;
    let l = reach_both(p);
    let (r, w) = black(p);
    f.poly(g, &block_both(-l, l, 0.9 * r, w));
}

/// ➔: the black arrow with a wider, shorter head.
fn wide_headed(g: &mut Draw, f: Frame) {
    let p = g.p;
    let l = reach(p);
    let (r, w) = black(p);
    let r = 1.18 * r;
    let xo = l - 0.75 * r;
    f.poly(g, &[pt(-l, -w), pt(xo, -w), pt(xo, -r), pt(l, 0.0), pt(xo, r), pt(xo, w), pt(-l, w)]);
}

/// ➝ ➞ ➛: a shaft and a filled triangle; `heavy` thickens the shaft, `narrow` draws the drafting point.
fn triangle_headed(g: &mut Draw, f: Frame, heavy: f64, narrow: bool) {
    let p = g.p;
    let l = reach(p);
    let h = head(p);
    let t = heavy * p.op;
    let (len, rise) = if narrow { (1.5 * h.len, 0.5 * h.rise) } else { (h.len, (0.62 + 0.18 * heavy) * h.rise) };
    f.poly(g, &[pt(l, 0.0), pt(l - len, rise), pt(l - len, -rise)]);
    shaft(g, f, -l, l - 0.6 * len, 0.0, t);
}

/// ➜: a heavy chevron at 45 degrees and a shaft, their free ends round.
fn round_tipped(g: &mut Draw, f: Frame) {
    let p = g.p;
    let l = reach(p);
    let t = 1.35 * p.op;
    let rc = 1.05 * chevron_rise(p) - t / 2.0; // the arms' centre lines end this far from the axis
    let xt = l - t / std::f64::consts::SQRT_2; // the centre lines meet here; the mitre reaches `l`
    let xo = xt - rc;
    f.stroke(g, &[knot(xo, rc, t).line(), knot(xt, 0.0, t).line(), knot(xo, -rc, t)]);
    shaft(g, f, -l + t / 2.0, xt - 0.5 * t, 0.0, t);
    for z in [pt(-l + t / 2.0, 0.0), pt(xo, rc), pt(xo, -rc)] {
        let z = f.z(z);
        g.dot(z.x, z.y, t / 2.0);
    }
}

// ---------------------------------------------------------------------------------------------------------------
// Arrows to a bar or a corner

/// ↸ ⇱ (and, turned, ⇲): a diagonal arrow pointing at a bar along the top of the arrows' square, and, with
/// `corner`, at the corner of that bar and one down the left.
fn to_corner(g: &mut Draw, f: Frame, corner: bool) {
    let p = g.p;
    let t = p.op;
    let l = reach(p);
    let gap = stop_gap(p);
    let e = 0.7 * tip(p); // how far the flat of the tip reaches past the tip's centre, along the bar
    let yb = l - t / 2.0;
    if corner {
        let arm = 1.5 * l;
        f.rect(g, -l, l - t, -l + arm, l);
        f.rect(g, -l, l - arm, -l + t, l);
    } else {
        f.rect(g, -l, l - t, l, l);
    }
    let y_tip = yb - t / 2.0 - gap - e;
    // the arrow runs as far across as down; pointing at a corner it runs from the corner to the far edge
    let d = if corner { 2.0 * l - t - gap - e - 0.5 * t } else { 2.0 * l / std::f64::consts::SQRT_2 };
    let x_tip = if corner { -l + t + gap + e } else { -d / 2.0 };
    let tail = pt(x_tip + d, y_tip - d);
    let mid = (pt(x_tip, y_tip) + tail) / 2.0;
    let a = Arrow { l: d / std::f64::consts::SQRT_2, ..Arrow::new(p) };
    draw(g, f.turned(mid, 135.0), &a);
}

// ---------------------------------------------------------------------------------------------------------------
// Marks over letters

/// The arrows over a letter: small, at the height of a mark over a capital, over the previous cell.
fn arrow_above(g: &mut Draw, tail: End, tip: End, left: bool) {
    let p = g.p;
    let t = 0.8 * pair_stroke(p);
    let h = small_head(p, t);
    let h = Head { len: 0.6 * h.len, rise: 0.6 * h.rise + 0.2 * t, ..h };
    let l = 0.66 * half_span(p);
    let y = p.cap + 54.0 + h.rise;
    let f = Frame { o: pt(-p.mid(), y), u: pt(1.0, 0.0), v: pt(0.0, 1.0) };
    let a = Arrow { tail, tip, l, h, t, ..Arrow::new(p) };
    draw(g, if left { f.back() } else { f }, &a);
    g.anchor("_top", -p.mid(), p.cap);
}

fn dots_above(g: &mut Draw, n: usize) {
    let p = g.p;
    let r = 0.6 * p.dot;
    let pitch = 2.0 * r + 0.5 * rel_gap(p);
    let y = p.cap + 54.0 + r;
    for i in 0..n {
        let x = -p.mid() + (i as f64 - (n as f64 - 1.0) / 2.0) * pitch;
        g.dot(x, y, r);
    }
    g.anchor("_top", -p.mid(), p.cap);
}

// ---------------------------------------------------------------------------------------------------------------
// The proportional family

const LONG: [char; 11] = ['⟵', '⟶', '⟷', '⟸', '⟹', '⟺', '⟻', '⟼', '⟽', '⟾', '⟿'];

/// The long arrows take a cell and a half in the proportional family; every other arrow keeps the master's cell.
pub fn fit(name: &str, p: &Params) -> Option<Fit> {
    LONG.iter().any(|&c| name_of(c) == name).then(|| Fit::new(1.5 * p.width))
}

// ---------------------------------------------------------------------------------------------------------------

/// A straight arrow in the registration table: character, heading, reflected in its line, tail, tip, shafts,
/// line, mark.
type Row = (char, f64, bool, End, End, usize, Line, Mark);

pub fn register(reg: &mut Registry) {
    use End::*;
    use Line::{Dashed as D, Solid as S, Wave as W, Zigzag as Z};
    use Mark::{None as N, Slash, Strokes};
    reg.module("arrows");
    // the straight arrows: character, heading, reflected in its line, tail, tip, shafts, line, mark
    #[rustfmt::skip]
    let rows: &[Row] = &[
        ('→', 0.0, false, Plain, Head, 1, S, N),
        ('↑', 90.0, false, Plain, Head, 1, S, N),
        ('←', 180.0, false, Plain, Head, 1, S, N),
        ('↓', -90.0, false, Plain, Head, 1, S, N),
        ('↗', 45.0, false, Plain, Head, 1, S, N),
        ('↖', 135.0, false, Plain, Head, 1, S, N),
        ('↙', -135.0, false, Plain, Head, 1, S, N),
        ('↘', -45.0, false, Plain, Head, 1, S, N),
        ('↔', 0.0, false, Head, Head, 1, S, N),
        ('↕', 90.0, false, Head, Head, 1, S, N),
        ('↛', 0.0, false, Plain, Head, 1, S, Slash),
        ('↚', 180.0, false, Plain, Head, 1, S, Slash),
        ('↮', 0.0, false, Head, Head, 1, S, Slash),
        ('↝', 0.0, false, Plain, Head, 1, W, N),
        ('↜', 180.0, true, Plain, Head, 1, W, N),
        ('↭', 0.0, false, Head, Head, 1, W, N),
        ('⇝', 0.0, false, Plain, Head, 1, Z, N),
        ('⇜', 180.0, true, Plain, Head, 1, Z, N),
        ('↣', 0.0, false, Feather, Head, 1, S, N),
        ('↢', 180.0, false, Feather, Head, 1, S, N),
        ('↠', 0.0, false, Plain, Two, 1, S, N),
        ('↞', 180.0, false, Plain, Two, 1, S, N),
        ('↟', 90.0, false, Plain, Two, 1, S, N),
        ('↡', -90.0, false, Plain, Two, 1, S, N),
        ('↦', 0.0, false, Bar, Head, 1, S, N),
        ('↤', 180.0, false, Bar, Head, 1, S, N),
        ('↥', 90.0, false, Bar, Head, 1, S, N),
        ('↧', -90.0, false, Bar, Head, 1, S, N),
        ('↪', 0.0, false, Hook, Head, 1, S, N),
        ('↩', 180.0, true, Hook, Head, 1, S, N),
        ('↼', 180.0, true, Plain, Barb, 1, S, N),
        ('↽', 180.0, false, Plain, Barb, 1, S, N),
        ('⇀', 0.0, false, Plain, Barb, 1, S, N),
        ('⇁', 0.0, true, Plain, Barb, 1, S, N),
        ('↾', 90.0, true, Plain, Barb, 1, S, N),
        ('↿', 90.0, false, Plain, Barb, 1, S, N),
        ('⇂', -90.0, false, Plain, Barb, 1, S, N),
        ('⇃', -90.0, true, Plain, Barb, 1, S, N),
        ('⇐', 180.0, false, Plain, Head, 2, S, N),
        ('⇑', 90.0, false, Plain, Head, 2, S, N),
        ('⇒', 0.0, false, Plain, Head, 2, S, N),
        ('⇓', -90.0, false, Plain, Head, 2, S, N),
        ('⇔', 0.0, false, Head, Head, 2, S, N),
        ('⇕', 90.0, false, Head, Head, 2, S, N),
        ('⇖', 135.0, false, Plain, Head, 2, S, N),
        ('⇗', 45.0, false, Plain, Head, 2, S, N),
        ('⇘', -45.0, false, Plain, Head, 2, S, N),
        ('⇙', -135.0, false, Plain, Head, 2, S, N),
        ('⇍', 180.0, false, Plain, Head, 2, S, Slash),
        ('⇏', 0.0, false, Plain, Head, 2, S, Slash),
        ('⇎', 0.0, false, Head, Head, 2, S, Slash),
        ('⤆', 180.0, false, Bar, Head, 2, S, N),
        ('⤇', 0.0, false, Bar, Head, 2, S, N),
        ('⇚', 180.0, false, Plain, Head, 3, S, N),
        ('⇛', 0.0, false, Plain, Head, 3, S, N),
        ('⭅', 180.0, false, Plain, Head, 4, S, N),
        ('⭆', 0.0, false, Plain, Head, 4, S, N),
        ('⇞', 90.0, false, Plain, Head, 1, S, Strokes(2)),
        ('⇟', -90.0, false, Plain, Head, 1, S, Strokes(2)),
        ('⇠', 180.0, false, Plain, Head, 1, D, N),
        ('⇡', 90.0, false, Plain, Head, 1, D, N),
        ('⇢', 0.0, false, Plain, Head, 1, D, N),
        ('⇣', -90.0, false, Plain, Head, 1, D, N),
        ('⇤', 180.0, false, Plain, ToBar, 1, S, N),
        ('⇥', 0.0, false, Plain, ToBar, 1, S, N),
        ('⇴', 0.0, false, Plain, Head, 1, S, Mark::Ring),
        ('⇷', 180.0, false, Plain, Head, 1, S, Strokes(1)),
        ('⇸', 0.0, false, Plain, Head, 1, S, Strokes(1)),
        ('⇹', 0.0, false, Head, Head, 1, S, Strokes(1)),
        ('⇺', 180.0, false, Plain, Head, 1, S, Strokes(2)),
        ('⇻', 0.0, false, Plain, Head, 1, S, Strokes(2)),
        ('⇼', 0.0, false, Head, Head, 1, S, Strokes(2)),
        ('⇽', 180.0, false, Plain, Open, 1, S, N),
        ('⇾', 0.0, false, Plain, Open, 1, S, N),
        ('⇿', 0.0, false, Open, Open, 1, S, N),
        ('⟵', 180.0, false, Plain, Head, 1, S, N),
        ('⟶', 0.0, false, Plain, Head, 1, S, N),
        ('⟷', 0.0, false, Head, Head, 1, S, N),
        ('⟻', 180.0, false, Bar, Head, 1, S, N),
        ('⟼', 0.0, false, Bar, Head, 1, S, N),
    ];
    // the long double arrows and the long squiggle
    #[rustfmt::skip]
    let long_rows: &[Row] = &[
        ('⟸', 180.0, false, Plain, Head, 2, S, N),
        ('⟹', 0.0, false, Plain, Head, 2, S, N),
        ('⟺', 0.0, false, Head, Head, 2, S, N),
        ('⟽', 180.0, false, Bar, Head, 2, S, N),
        ('⟾', 0.0, false, Bar, Head, 2, S, N),
        ('⟿', 0.0, false, Plain, Head, 1, Z, N),
    ];
    for &(c, heading, flipped, tail, tip, rails, line, mark) in rows.iter().chain(long_rows) {
        let long = LONG.contains(&c);
        reg.ch(c, move |g: &mut Draw| {
            let p = g.p;
            let mut a = Arrow { line, mark, ..Arrow::new(p).rails(rails, p).ends(tail, tip, p) };
            if long {
                a.l = reach_long(p);
            }
            let f = Frame::new(p, heading);
            draw(g, if flipped { f.flipped() } else { f }, &a);
        });
    }

    // two small arrows side by side: character, heading, whether the first and the second point back
    for (c, heading, r1, r2) in [
        ('⇄', 0.0, false, true),
        ('⇆', 0.0, true, false),
        ('⇉', 0.0, false, false),
        ('⇇', 180.0, false, false),
        ('⇈', 90.0, false, false),
        ('⇊', -90.0, false, false),
        ('⇅', 90.0, false, true),
        ('⇵', 90.0, true, false),
    ] {
        reg.ch(c, move |g: &mut Draw| {
            let p = g.p;
            let f = Frame::new(p, heading);
            let a = Arrow::new(p).small(p);
            let half = pair_pitch(p) / 2.0;
            for (y, back) in [(half, r1), (-half, r2)] {
                let fr = f.at(0.0, y);
                draw(g, if back { fr.back().flipped() } else { fr }, &a);
            }
        });
    }
    reg.ch('↹', |g: &mut Draw| {
        let p = g.p;
        let f = Frame::new(p, 180.0);
        let a = Arrow::new(p).small(p).ends(End::Plain, End::ToBar, p);
        let a = Arrow { l: reach(p), ..a };
        let half = pair_pitch(p) / 2.0;
        draw(g, f.at(0.0, -half), &a);
        draw(g, f.at(0.0, half).back().flipped(), &a);
    });
    // two small harpoons the bars of = apart, their barbs outwards: character, whether the upper and the lower
    // point left
    for (c, l1, l2) in [('⇌', false, true), ('⇋', true, false), ('⥤', false, false)] {
        reg.ch(c, move |g: &mut Draw| {
            let p = g.p;
            let f = Frame::new(p, 0.0);
            let a = Arrow::new(p).small(p).ends(End::Plain, End::Barb, p);
            let half = equal_pitch(p) / 2.0;
            let top = f.at(0.0, half);
            let bot = f.at(0.0, -half).flipped();
            draw(g, if l1 { top.back() } else { top }, &a);
            draw(g, if l2 { bot.back() } else { bot }, &a);
        });
    }
    reg.ch('↨', |g: &mut Draw| {
        let p = g.p;
        let t = p.op;
        let a = Arrow::new(p).ends(End::Head, End::Head, p);
        // ↕ over a base as wide as its heads, the two together centred on the axis
        let lift = (t + stop_gap(p)) / 2.0;
        let y = p.axis + lift - a.l - stop_gap(p);
        g.rect(p.mid() - a.h.rise, y - t, p.mid() + a.h.rise, y);
        draw(g, Frame::new(p, 90.0).at(lift, 0.0), &a);
    });

    // corners
    reg.ch('↳', |g: &mut Draw| corner_tall(g, Frame::new(g.p, 0.0)));
    reg.ch('↲', |g: &mut Draw| corner_tall(g, Frame::new(g.p, 180.0).flipped()));
    reg.ch('↱', |g: &mut Draw| corner_tall(g, Frame::new(g.p, 0.0).flipped()));
    reg.ch('↰', |g: &mut Draw| corner_tall(g, Frame::new(g.p, 180.0)));
    reg.ch('↴', |g: &mut Draw| corner_tall(g, Frame::new(g.p, -90.0).flipped()));
    reg.ch('↵', |g: &mut Draw| corner_return(g, Frame::new(g.p, 180.0).flipped()));

    // circles
    reg.ch('↶', |g: &mut Draw| semicircle(g, false));
    reg.ch('↷', |g: &mut Draw| semicircle(g, true));
    reg.ch('↺', |g: &mut Draw| open_circle(g, false));
    reg.ch('↻', |g: &mut Draw| open_circle(g, true));
    reg.ch('⟲', |g: &mut Draw| g.same_as_char('↺'));
    reg.ch('⟳', |g: &mut Draw| g.same_as_char('↻'));

    // to a bar or a corner
    reg.ch('↸', |g: &mut Draw| to_corner(g, Frame::new(g.p, 0.0), false));
    reg.ch('⇱', |g: &mut Draw| to_corner(g, Frame::new(g.p, 0.0), true));
    reg.ch('⇲', |g: &mut Draw| to_corner(g, Frame::new(g.p, 180.0), true));

    // white and black
    for (c, heading) in [('⇨', 0.0), ('⇧', 90.0), ('⇦', 180.0), ('⇩', -90.0)] {
        reg.ch(c, move |g: &mut Draw| white_arrow(g, Frame::new(g.p, heading)));
    }
    reg.ch('⇳', |g: &mut Draw| white_arrow_both(g, Frame::new(g.p, 90.0)));
    reg.ch('⇪', |g: &mut Draw| white_arrow_over(g, Frame::new(g.p, 90.0), Base::Box));
    reg.ch('⇫', |g: &mut Draw| white_arrow_over(g, Frame::new(g.p, 90.0), Base::Pedestal));
    reg.ch('⇬', |g: &mut Draw| white_arrow_over(g, Frame::new(g.p, 90.0), Base::PedestalBar));
    reg.ch('⇭', |g: &mut Draw| white_arrow_over(g, Frame::new(g.p, 90.0), Base::PedestalStem));
    reg.ch('⇰', |g: &mut Draw| white_arrow_over(g, Frame::new(g.p, 0.0), Base::Wall));
    for (c, heading) in [('➡', 0.0), ('⬆', 90.0), ('⬅', 180.0), ('⬇', -90.0)] {
        reg.ch(c, move |g: &mut Draw| black_arrow(g, Frame::new(g.p, heading)));
    }
    reg.ch('⬌', |g: &mut Draw| black_arrow_both(g, Frame::new(g.p, 0.0)));
    reg.ch('⬍', |g: &mut Draw| black_arrow_both(g, Frame::new(g.p, 90.0)));
    reg.ch('➔', |g: &mut Draw| wide_headed(g, Frame::new(g.p, 0.0)));
    reg.ch('➜', |g: &mut Draw| round_tipped(g, Frame::new(g.p, 0.0)));
    reg.ch('➝', |g: &mut Draw| triangle_headed(g, Frame::new(g.p, 0.0), 1.0, false));
    reg.ch('➞', |g: &mut Draw| triangle_headed(g, Frame::new(g.p, 0.0), 1.6, false));
    reg.ch('➛', |g: &mut Draw| triangle_headed(g, Frame::new(g.p, 0.0), 0.8, true));

    // over letters
    reg.code(0x20D6, Opt::MARK, |g: &mut Draw| arrow_above(g, End::Plain, End::Head, true));
    reg.code(0x20D7, Opt::MARK, |g: &mut Draw| arrow_above(g, End::Plain, End::Head, false));
    reg.code(0x20E1, Opt::MARK, |g: &mut Draw| arrow_above(g, End::Head, End::Head, false));
    reg.code(0x20DB, Opt::MARK, |g: &mut Draw| dots_above(g, 3));
    reg.code(0x20DC, Opt::MARK, |g: &mut Draw| dots_above(g, 4));
}
