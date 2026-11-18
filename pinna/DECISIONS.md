# Decisions

## D1. Reissner-Mindlin plate, not Euler-Bernoulli beam or Kirchhoff plate

Tuned bars are thick near the ends and thin in the middle, and their upper partials
sit well below thin-theory values because of shear and rotary inertia. A beam model
also cannot produce the torsional modes that sit between the tuned partials, or
handle a plate or a drawn outline. Rejected: a Timoshenko beam (no torsion, no
arbitrary outline); 3D solid elements (far slower in a browser for little gain at
these thickness ratios).

## D2. Three-node triangle with constant bending and one-point shear

Triangles mesh any outline. Shear is integrated at the centroid with a stabilising
factor that depends on element size over thickness, which avoids locking on thin
plates. The reference tests fix the accuracy: Leissa's free square plate, the free
circular plate, and bars against beam theory. Rejected: MITC or DKT elements, which
are more accurate per node but would have taken longer to validate.

## D3. Own linear algebra

Skyline Cholesky with reverse Cuthill-McKee ordering and subspace iteration, written
here. The systems are a few thousand unknowns, the bandwidth is small for bars, and
warm-starting the subspace makes each tuning step cheap. Rejected: a WebAssembly
build of ARPACK or Eigen (a build step and a large download for no speed that
matters at this size).

## D4. Analytic thickness sensitivities drive the tuner

Element stiffness is cubic and linear in thickness and mass is linear and cubic, so
the derivative of each eigenvalue with respect to each element's thickness is exact
and costs one pass over the elements. Rejected: finite differences (one solve per
control point per step) and derivative-free search.

## D5. The cut is a smooth symmetric profile with bounds

Control points along the length (or radius) feed a spline, mirrored about the
centre, and the depth is held between zero and 80% of the blank. The tuner is
Gauss-Newton on the error in cents with a smoothness penalty that is relaxed as it
converges, and control points at a bound are held there. Rejected: free thickness
per element (not something a maker can cut) and an asymmetric profile (no benefit
for a symmetric bar).

## D6. Modal synthesis for sound

The solver already gives frequencies and shapes, so a strike is the sum of the
modes weighted by shape at the strike point and by the spectrum of a half-sine
contact. Decay comes from the material loss factor. Rejected: time-stepping the
plate (slow and adds numerical dispersion).

## D7. Preact, signals and three.js; no Effect code yet

The interface is small and state is a handful of signals. The solver runs in a
worker. `effect` is installed per the repository rule but nothing here needs it
yet: the core is synchronous numerics with no services or failures to model.

## D8. Fonts are copied from Rachis

`public/fonts/` holds Rachis and Rachis Mono from `rachis/fonts/`. Copied, not
linked, so the project builds on its own.
