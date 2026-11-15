//! Glyphs, the registry of glyph programs, and the canvas a program draws on.
//!
//! A glyph program is a function that takes a [`Draw`] and adds strokes and shapes to it. It reads every
//! measurement from `Draw::p`, the parameters of the master being drawn, and it must not branch on them: the same
//! program has to produce the same structure for every master, because the variable font interpolates between
//! them.

use std::collections::{BTreeMap, HashMap};

use crate::geom::{V, pt, segment_bounds};
use crate::names::{name_of, name_of_code};
use crate::params::Params;
use crate::pen::{Contour, Knot, expand, polygon, rect, sheared, superellipse};

#[derive(Clone, Debug, Default)]
pub struct Glyph {
    pub name: String,
    pub advance: f64,
    pub unicodes: Vec<u32>,
    pub contours: Vec<Contour>,
    /// Other glyphs placed in this one: (name, offset).
    pub components: Vec<(String, V)>,
    pub anchors: BTreeMap<String, V>,
    pub mark: bool,
    /// The strokes the outline came from, as drawn: for diagrams, not for the font.
    pub skeletons: Vec<(Vec<Knot>, bool)>,
    /// What went wrong while the program ran. A glyph with errors is not built into a font.
    pub errors: Vec<String>,
}

impl Glyph {
    pub fn bounds(&self) -> Option<(f64, f64, f64, f64)> {
        segment_bounds(self.contours.iter().flat_map(|c| c.segs.iter()))
    }

    /// The glyph's structure, which must agree between the masters of a variable font.
    pub fn signature(&self) -> String {
        let mut parts: Vec<String> = self.contours.iter().map(Contour::signature).collect();
        parts.extend(self.components.iter().map(|(name, _)| format!("@{name}")));
        parts.extend(self.anchors.keys().map(|name| format!("#{name}")));
        parts.join(" ")
    }
}

/// The canvas of one glyph in one master.
pub struct Draw<'a> {
    pub p: &'a Params,
    pub glyph: Glyph,
    slope: f64,
}

impl<'a> Draw<'a> {
    pub fn new(p: &'a Params, name: &str, advance: f64, upright: bool) -> Draw<'a> {
        let slope = if upright {
            0.0
        } else {
            p.slant.to_radians().tan()
        };
        Draw {
            p,
            glyph: Glyph {
                name: name.into(),
                advance,
                ..Glyph::default()
            },
            slope,
        }
    }

    fn shear_point(&self, z: V) -> V {
        pt(z.x + self.slope * (z.y - self.p.slant_origin()), z.y)
    }

    fn stroke_any(&mut self, knots: &[Knot], closed: bool) {
        let ks: Vec<Knot> = knots
            .iter()
            .map(|k| sheared(k, self.slope, self.p.slant_origin()))
            .collect();
        match expand(&ks, closed) {
            Ok(contours) => self.glyph.contours.extend(contours),
            Err(e) => self.glyph.errors.push(e),
        }
        self.glyph.skeletons.push((ks, closed));
    }

    /// Add the outline of the open stroke through `knots`.
    pub fn stroke(&mut self, knots: &[Knot]) {
        self.stroke_any(knots, false);
    }

    /// Add the outline of the closed stroke through `knots`: an outer and an inner contour.
    pub fn stroke_closed(&mut self, knots: &[Knot]) {
        self.stroke_any(knots, true);
    }

    /// Add a filled contour. An italic slants it.
    pub fn add(&mut self, contour: Contour) {
        if self.slope != 0.0 {
            let (slope, origin) = (self.slope, self.p.slant_origin());
            self.glyph
                .contours
                .push(contour.mapped(|z| pt(z.x + slope * (z.y - origin), z.y)));
        } else {
            self.glyph.contours.push(contour);
        }
    }

    /// Add a filled contour that an italic leaves as it is.
    pub fn add_upright(&mut self, contour: Contour) {
        self.glyph.contours.push(contour);
    }

    pub fn rect(&mut self, x0: f64, y0: f64, x1: f64, y1: f64) {
        self.add(rect(x0, y0, x1, y1));
    }

    pub fn poly(&mut self, points: &[V]) {
        self.add(polygon(points));
    }

    /// A round dot of radius `r`. An italic moves it along the slant but does not shear it.
    pub fn dot(&mut self, cx: f64, cy: f64, r: f64) {
        self.dot_xy(cx, cy, r, r, self.p.dot_k);
    }

    /// A round dot with radii `rx`, `ry` and squareness `k`.
    pub fn dot_xy(&mut self, cx: f64, cy: f64, rx: f64, ry: f64, k: f64) {
        let c = self.shear_point(pt(cx, cy));
        self.glyph.contours.push(superellipse(c.x, c.y, rx, ry, k));
    }

    /// Place the glyph of character `c` as a component, moved by (dx, dy) in upright coordinates.
    pub fn use_char(&mut self, c: char, dx: f64, dy: f64) {
        self.use_glyph(&name_of(c), dx, dy);
    }

    /// Place the glyph called `name` as a component, moved by (dx, dy) in upright coordinates.
    pub fn use_glyph(&mut self, name: &str, dx: f64, dy: f64) {
        self.glyph
            .components
            .push((name.into(), pt(dx + self.slope * dy, dy)));
    }

    pub fn anchor(&mut self, name: &str, x: f64, y: f64) {
        let z = self.shear_point(pt(x, y));
        self.glyph.anchors.insert(name.into(), z);
    }
}

pub type Program = Box<dyn Fn(&mut Draw) + Send + Sync>;

/// How a glyph is registered. `upright` keeps it out of the italic's slant (box drawing, blocks). `mark` makes it
/// a combining mark with no advance.
#[derive(Clone, Copy, Debug, Default, PartialEq)]
pub struct Opt {
    pub upright: bool,
    pub mark: bool,
    pub advance: Option<f64>,
}

impl Opt {
    pub const UPRIGHT: Opt = Opt {
        upright: true,
        mark: false,
        advance: None,
    };
    pub const MARK: Opt = Opt {
        upright: false,
        mark: true,
        advance: None,
    };
}

pub struct Spec {
    pub name: String,
    pub unicodes: Vec<u32>,
    pub program: Program,
    pub opt: Opt,
    pub module: &'static str,
}

/// The glyph programs of a typeface, in the order they were registered.
#[derive(Default)]
pub struct Registry {
    pub specs: Vec<Spec>,
    index: HashMap<String, usize>,
    module: &'static str,
}

impl Registry {
    pub fn new() -> Registry {
        Registry::default()
    }

    /// Name the module whose glyphs are registered next.
    pub fn module(&mut self, name: &'static str) {
        self.module = name;
    }

    /// Register a program for one character under its canonical name.
    pub fn ch(&mut self, c: char, program: impl Fn(&mut Draw) + Send + Sync + 'static) {
        self.glyph(&name_of(c), &[c as u32], Opt::default(), program);
    }

    /// Register a program for one character, with options.
    pub fn ch_with(
        &mut self,
        c: char,
        opt: Opt,
        program: impl Fn(&mut Draw) + Send + Sync + 'static,
    ) {
        self.glyph(&name_of(c), &[c as u32], opt, program);
    }

    /// Register a program for one code point, with options.
    pub fn code(&mut self, cp: u32, opt: Opt, program: impl Fn(&mut Draw) + Send + Sync + 'static) {
        self.glyph(&name_of_code(cp), &[cp], opt, program);
    }

    /// Register an unencoded glyph: an alternate (`zero.dot`) or a special glyph (`.notdef`).
    pub fn named(&mut self, name: &str, program: impl Fn(&mut Draw) + Send + Sync + 'static) {
        self.glyph(name, &[], Opt::default(), program);
    }

    pub fn glyph(
        &mut self,
        name: &str,
        unicodes: &[u32],
        opt: Opt,
        program: impl Fn(&mut Draw) + Send + Sync + 'static,
    ) {
        assert!(
            !self.index.contains_key(name),
            "glyph {name:?} is defined twice ({} and {})",
            self.specs[self.index[name]].module,
            self.module
        );
        self.index.insert(name.into(), self.specs.len());
        self.specs.push(Spec {
            name: name.into(),
            unicodes: unicodes.to_vec(),
            program: Box::new(program),
            opt,
            module: self.module,
        });
    }

    pub fn get(&self, name: &str) -> Option<&Spec> {
        self.index.get(name).map(|&i| &self.specs[i])
    }

    pub fn len(&self) -> usize {
        self.specs.len()
    }

    pub fn is_empty(&self) -> bool {
        self.specs.is_empty()
    }

    /// The glyph for a character, if one is registered.
    pub fn for_char(&self, c: char) -> Option<&Spec> {
        self.specs.iter().find(|s| s.unicodes.contains(&(c as u32)))
    }
}

/// Run one glyph program for the master `p`.
pub fn build(spec: &Spec, p: &Params) -> Glyph {
    let advance = if spec.opt.mark {
        0.0
    } else {
        spec.opt.advance.unwrap_or(p.width)
    };
    let mut g = Draw::new(p, &spec.name, advance, spec.opt.upright);
    (spec.program)(&mut g);
    g.glyph.unicodes = spec.unicodes.clone();
    g.glyph.mark = spec.opt.mark;
    g.glyph
}

/// Every registered glyph drawn for the master `p`, in registration order.
pub fn build_all(registry: &Registry, p: &Params) -> Vec<Glyph> {
    registry.specs.iter().map(|s| build(s, p)).collect()
}
