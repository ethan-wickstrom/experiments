# Pinna

Pinna is a browser workbench for designing struck instruments: marimba, vibraphone and
xylophone bars, plates, discs, and any outline you draw.

You choose an outline, a material and a thickness. Pinna solves the piece's vibration
modes and shows each one, with sand collecting on the lines that stay still. Click the
piece to strike it there and hear it. Set a pitch and the ratios the partials should
have, and Pinna computes the undercut that puts them there, the cut a marimba maker
finds by ear and sandpaper.

## Run it

```sh
bun install
bun run dev      # development server
bun run build    # production build in dist/
bun run preview  # serve the production build
```

## Use it

- **Start from** a preset, or pick Bar, Disc, Polygon or Drawn. In Drawn, drag corners,
  double-click an edge to add one and a corner to remove it.
- **Click the piece** to strike it. Drag to turn it. Space strikes again.
- **Hover a partial** in the table or spectrum to see its shape; click to hold it.
- **Compute the undercut** tunes the listed ratios. "Bending partials" counts only the
  modes that bend along the bar, which is how bars are tuned; "Every partial" counts
  all of them.
- **Drag the undercut handles** to carve by hand.
- **Files** saves and opens a design, exports the cut profile as CSV (position and
  remaining thickness in millimetres), and exports the last strike as WAV.

## What it computes

- The piece is a Reissner-Mindlin plate with orthotropic material and a thickness
  that varies over the surface, so thick bars and wood with a grain direction are
  covered. Edges are free.
- The outline is meshed into triangles and the lowest modes come from subspace
  iteration on a shifted skyline Cholesky factor.
- Each mode carries the exact derivative of its frequency with respect to the
  thickness of every element. The tuner uses these in a bounded Gauss-Newton
  iteration over a smooth, symmetric cut profile.
- A strike is a sum of the modes, each weighted by its shape at the point struck and
  by the spectrum of a mallet contact of the chosen length, and decaying at the
  material's loss factor.

## Limits

- Material values are handbook figures. Wood varies by tens of percent between
  blanks, so measure the blank before cutting from a profile.
- Supports, cord holes and resonators are not modelled.
- The cut varies along the length or with radius only, not across the width.
- The sound has not been compared with recordings of real bars.

The checks are `bun test`, `bun run check`, `bun run lint`, `bun run format` and
`bun run build`. See [the decisions](DECISIONS.md) and [the ledger](LEDGER.md).
