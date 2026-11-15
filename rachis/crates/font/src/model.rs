//! The OpenType variation model: how masters placed in a design space become regions and deltas.
//!
//! A variable font stores one default master and, for every other master, a region of the design space (a tent
//! on each axis it involves) with the difference that master makes. A rasteriser adds the differences back,
//! each scaled by how far inside its region the requested location lies. This module computes the regions and
//! the differences, as fontTools' `varLib.models.VariationModel` does, and evaluates the model at a location,
//! which is how the static fonts are made: a static font is the variable font at one point.
//!
//! Locations are normalised: one value per axis, 0 at the default, -1 and 1 at the axis's ends.

/// A tent on one axis: where a master starts to act, where it acts fully, where it stops.
pub type Tent = (f64, f64, f64);

#[derive(Clone, Debug)]
pub struct Model {
    axes: usize,
    /// The masters in model order, as indices into the caller's list.
    order: Vec<usize>,
    /// The region of each master, in model order: one tent per axis, `None` where the axis is not involved.
    supports: Vec<Vec<Option<Tent>>>,
    /// For each master in model order, the earlier masters whose regions it lies in, with their scalars.
    weights: Vec<Vec<(usize, f64)>>,
}

impl Model {
    /// A model for masters at `locations`. One of them must be the default (all zeros), and no two may coincide.
    pub fn new(locations: &[Vec<f64>]) -> Result<Model, String> {
        let axes = locations.first().map_or(0, Vec::len);
        if locations.iter().any(|l| l.len() != axes) {
            return Err("every location needs a value for every axis".into());
        }
        if !locations.iter().any(|l| l.iter().all(|&v| v == 0.0)) {
            return Err("no master is at the default location".into());
        }
        for (i, a) in locations.iter().enumerate() {
            if locations[..i].contains(a) {
                return Err("two masters share a location".into());
            }
        }

        // The values at which masters sit alone on an axis.
        let mut axis_points: Vec<Vec<f64>> = vec![vec![0.0]; axes];
        for loc in locations {
            let involved: Vec<usize> = (0..axes).filter(|&a| loc[a] != 0.0).collect();
            if let [a] = involved[..] {
                axis_points[a].push(loc[a]);
            }
        }
        type Key = (usize, isize, Vec<usize>, Vec<i8>, Vec<f64>);
        let key = |loc: &Vec<f64>| -> Key {
            let involved: Vec<usize> = (0..axes).filter(|&a| loc[a] != 0.0).collect();
            let on_point = involved
                .iter()
                .filter(|&&a| axis_points[a].contains(&loc[a]))
                .count();
            let signs = involved
                .iter()
                .map(|&a| if loc[a] < 0.0 { -1 } else { 1 })
                .collect();
            let sizes = involved.iter().map(|&a| loc[a].abs()).collect();
            (involved.len(), -(on_point as isize), involved, signs, sizes)
        };
        let mut order: Vec<usize> = (0..locations.len()).collect();
        order.sort_by(|&i, &j| {
            let (a, b) = (key(&locations[i]), key(&locations[j]));
            a.0.cmp(&b.0)
                .then(a.1.cmp(&b.1))
                .then(a.2.cmp(&b.2))
                .then(a.3.cmp(&b.3))
                .then(a.4.partial_cmp(&b.4).unwrap_or(std::cmp::Ordering::Equal))
        });
        let sorted: Vec<&Vec<f64>> = order.iter().map(|&i| &locations[i]).collect();

        // Each master's region starts as the whole stretch from the default to the axis's end on its side.
        let mut lo = vec![0.0f64; axes];
        let mut hi = vec![0.0f64; axes];
        for loc in &sorted {
            for a in 0..axes {
                lo[a] = lo[a].min(loc[a]);
                hi[a] = hi[a].max(loc[a]);
            }
        }
        let regions: Vec<Vec<Option<Tent>>> = sorted
            .iter()
            .map(|loc| {
                (0..axes)
                    .map(|a| match loc[a] {
                        v if v > 0.0 => Some((0.0, v, hi[a])),
                        v if v < 0.0 => Some((lo[a], v, 0.0)),
                        _ => None,
                    })
                    .collect()
            })
            .collect();

        // Then earlier masters on the same axes that fall inside it cut it down.
        let mut supports: Vec<Vec<Option<Tent>>> = Vec::with_capacity(regions.len());
        for (i, start) in regions.iter().enumerate() {
            let mut region = start.clone();
            for prev in &regions[..i] {
                if (0..axes).any(|a| prev[a].is_some() != region[a].is_some()) {
                    continue; // a master on other axes does not take part
                }
                let inside = (0..axes).all(|a| match (region[a], prev[a]) {
                    (Some((lower, peak, upper)), Some((_, p, _))) => {
                        p == peak || (lower < p && p < upper)
                    }
                    _ => true,
                });
                if !inside {
                    continue;
                }
                // Cut in the direction with the largest range ratio; on a tie, in all such directions.
                let mut best: Vec<(usize, Tent)> = Vec::new();
                let mut best_ratio = -1.0;
                for a in 0..axes {
                    let (Some((lower, peak, upper)), Some((_, val, _))) = (region[a], prev[a])
                    else {
                        continue;
                    };
                    let (cut, ratio) = if val < peak {
                        ((val, peak, upper), (val - peak) / (lower - peak))
                    } else if peak < val {
                        ((lower, peak, val), (val - peak) / (upper - peak))
                    } else {
                        continue; // the box cannot be cut in this direction
                    };
                    if ratio > best_ratio {
                        best.clear();
                        best_ratio = ratio;
                    }
                    if ratio == best_ratio {
                        best.push((a, cut));
                    }
                }
                for (a, cut) in best {
                    region[a] = Some(cut);
                }
            }
            supports.push(region);
        }

        let weights = sorted
            .iter()
            .enumerate()
            .map(|(i, loc)| {
                supports[..i]
                    .iter()
                    .enumerate()
                    .filter_map(|(j, support)| {
                        let s = scalar(loc, support);
                        (s != 0.0).then_some((j, s))
                    })
                    .collect()
            })
            .collect();
        Ok(Model {
            axes,
            order,
            supports,
            weights,
        })
    }

    pub fn axis_count(&self) -> usize {
        self.axes
    }

    /// How many masters the model has, the default included.
    pub fn len(&self) -> usize {
        self.order.len()
    }

    pub fn is_empty(&self) -> bool {
        self.order.is_empty()
    }

    /// The regions of the non-default masters, in model order: one tent per axis ((0, 0, 0) where the axis is
    /// not involved).
    pub fn regions(&self) -> Vec<Vec<Tent>> {
        self.supports[1..]
            .iter()
            .map(|s| s.iter().map(|t| t.unwrap_or((0.0, 0.0, 0.0))).collect())
            .collect()
    }

    /// The differences each master makes. `values` are in the caller's master order; the result is in model
    /// order, and its first entry is the default master's value itself.
    pub fn deltas(&self, values: &[f64]) -> Vec<f64> {
        let mut out: Vec<f64> = Vec::with_capacity(values.len());
        for (i, weights) in self.weights.iter().enumerate() {
            let mut delta = values[self.order[i]];
            for &(j, w) in weights {
                delta -= out[j] * w;
            }
            out.push(delta);
        }
        out
    }

    /// The weight of each master's difference at `location`, in model order.
    pub fn scalars(&self, location: &[f64]) -> Vec<f64> {
        self.supports.iter().map(|s| scalar(location, s)).collect()
    }

    /// The value at `location`, from the master values in the caller's order.
    pub fn interpolate(&self, values: &[f64], location: &[f64]) -> f64 {
        self.deltas(values)
            .iter()
            .zip(self.scalars(location))
            .map(|(d, s)| d * s)
            .sum()
    }
}

/// How much of a master's difference applies at `location`: 1 at the region's peak, 0 outside the region.
fn scalar(location: &[f64], support: &[Option<Tent>]) -> f64 {
    let mut out = 1.0;
    for (a, tent) in support.iter().enumerate() {
        let Some((lower, peak, upper)) = *tent else {
            continue;
        };
        if peak == 0.0 || lower > peak || peak > upper || (lower < 0.0 && upper > 0.0) {
            continue;
        }
        let v = location[a];
        if v == peak {
            continue;
        }
        if v <= lower || upper <= v {
            return 0.0;
        }
        out *= if v < peak {
            (v - lower) / (peak - lower)
        } else {
            (v - upper) / (peak - upper)
        };
    }
    out
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn two_ends_of_one_axis() {
        let m = Model::new(&[vec![-1.0], vec![0.0], vec![1.0]]).unwrap();
        assert_eq!(
            m.regions(),
            vec![vec![(-1.0, -1.0, 0.0)], vec![(0.0, 1.0, 1.0)]]
        );
        // values in the caller's order: light 60, regular 88, bold 134
        assert_eq!(m.deltas(&[60.0, 88.0, 134.0]), vec![88.0, -28.0, 46.0]);
        assert_eq!(m.interpolate(&[60.0, 88.0, 134.0], &[0.5]), 111.0);
        assert_eq!(m.interpolate(&[60.0, 88.0, 134.0], &[-0.5]), 74.0);
        assert_eq!(m.interpolate(&[60.0, 88.0, 134.0], &[1.0]), 134.0);
    }

    #[test]
    fn an_intermediate_master_cuts_the_region_beyond_it() {
        let m = Model::new(&[vec![0.0], vec![0.5], vec![1.0]]).unwrap();
        assert_eq!(
            m.regions(),
            vec![vec![(0.0, 0.5, 1.0)], vec![(0.5, 1.0, 1.0)]]
        );
        // a value that is not linear in the axis is still reproduced at every master
        let values = [10.0, 30.0, 40.0];
        for (loc, want) in [
            (0.0, 10.0),
            (0.5, 30.0),
            (1.0, 40.0),
            (0.25, 20.0),
            (0.75, 35.0),
        ] {
            assert!((m.interpolate(&values, &[loc]) - want).abs() < 1e-12);
        }
    }

    #[test]
    fn a_corner_master_holds_only_what_the_axes_do_not_explain() {
        // default, the end of each axis, and the corner
        let m = Model::new(&[
            vec![0.0, 0.0],
            vec![1.0, 0.0],
            vec![0.0, 1.0],
            vec![1.0, 1.0],
        ])
        .unwrap();
        let d = m.deltas(&[100.0, 110.0, 130.0, 145.0]);
        assert_eq!(d, vec![100.0, 10.0, 30.0, 5.0]);
        assert!(
            (m.interpolate(&[100.0, 110.0, 130.0, 145.0], &[0.5, 0.5])
                - (100.0 + 5.0 + 15.0 + 1.25))
                .abs()
                < 1e-12
        );
    }

    #[test]
    fn a_model_needs_a_default_and_distinct_masters() {
        assert!(Model::new(&[vec![1.0], vec![-1.0]]).is_err());
        assert!(Model::new(&[vec![0.0], vec![1.0], vec![1.0]]).is_err());
    }
}
