# Drawing glyphs

How a glyph of this typeface is written, checked and looked at. Read `design.md` first for what the typeface is; this file is the working method.

## The model

A glyph is a program. It receives a canvas `g` and adds strokes and shapes to it. A stroke is a list of knots: points on the stroke's centre line, each with the pen's breadth there. The kernel draws a smooth centre line through the knots (a Hobby spline, straight where a knot says so) and returns the outline the pen leaves. Nothing is drawn by hand as an outline unless it is a polygon or a dot.

```python
from rachis.geom import pt, unit
from rachis.glyph import Draw, Knot, glyph
from rachis.parts import arch, vstem


@glyph("n", "n")  # glyph name, then the characters it encodes
def n(g: Draw) -> None:
    p = g.p  # the parameters of the master being drawn
    g.stroke(*vstem(p.xl, 0, p.xh, p.stem))
    g.stroke(*arch(p, p.xl, p.xr, p.xh + p.over, 0))
```

`Knot(z, w, pen=None, dir=None, line=False, k=None, t_in=1, t_out=1)`:

- `z`: the point, `pt(x, y)`.
- `w`: the pen's breadth at the knot. The breadth varies smoothly between knots.
- `pen`: the angle of the pen's edge, as a line. `pen=0` is a horizontal edge: it cuts a vertical or diagonal stroke flat, parallel to the baseline. `pen=90` is a vertical edge: it cuts a horizontal or curved stroke plumb. `None` holds the pen perpendicular to the path, which is what the inside of a curve wants.
- `dir`: the direction of travel through the knot in degrees (0 right, 90 up, 180 left, -90 down). Give it at every extreme of a curve (the top of a bowl travels at 0 or 180, its side at 90 or -90). `None` lets the spline choose.
- `line=True`: the segment from this knot to the next is straight. A curve that follows a straight segment leaves it smoothly unless the knot gives another `dir`.
- `k`: makes the curve from this knot to the next a superelliptic corner, with its handles at the fraction `k` of the way to the point where the two tangents meet. Use `p.sq` for bowls and shoulders. Without `k` the segment is a Hobby curve, which is right for S-shaped and diagonal transitions.

With a fixed `pen`, `w` is measured along the pen's edge, not across the stroke. `parts.cut(x, y, t, dir)` makes a knot with a vertical cut whose stroke is `t` thick, and `parts.diag(x0, y0, x1, y1, t)` makes a straight stroke `t` thick cut flat at both ends.

Other canvas calls: `g.poly(points)` for a polygon (pointed vertices: `parts.vee`), `g.rect(x0, y0, x1, y1)`, `g.dot(cx, cy, rx, ry=None)` for a round dot, `g.use(name, dx, dy)` to place another glyph as a component, `g.anchor(name, x, y)` for mark attachment.

## Rules

1. Every number comes from `g.p` or is a proportion of something in `g.p`. A stroke's thickness is `p.stem`, `p.hair`, `p.cap_stem`, `p.cap_hair` or `p.op`, or a stated fraction of one of them. Positions may use fixed design offsets, but an offset that must grow with weight (a counter, a gap, a radius near a stroke) is written in terms of the strokes.
2. Never branch on weight. The variable font interpolates between the Light, Regular and Bold masters, so the same program must produce the same sequence of strokes, knots and shapes in all three. `if p.stem > 100` is forbidden; a number that should differ between weights becomes a parameter. Branching on `p.italic` is allowed: upright and italic are separate fonts.
3. Cuts are aligned to the axes. A stem ends in a horizontal cut. A diagonal ends in a horizontal cut. A curved stroke ends in a vertical cut. No terminal is cut at an arbitrary angle, and there are no ball or flared terminals.
4. Round shapes overshoot flat ones by `p.over` at the baseline, the x-height and the cap height. Pointed vertices do too, or are flattened to at least a third of a stem.
5. Bowls and shoulders are superelliptic: `k=p.sq`. A bowl is `p.stem` thick at its sides and `p.hair` thick at its top and bottom.
6. Where an arch or bowl leaves a stem it is thin: `p.join * stem`. Start the stroke inside the stem so that the join is hidden (see `parts.arch`).
7. Stay in the cell. The advance is `p.width` (600) for every glyph except combining marks (0). Outlines stay within x = 0 … 600 unless the glyph is meant to connect to its neighbours (box drawing). Letters keep about `p.sb` clear beside a straight stem and `p.sb_round` beside a round side; the heavier the weight, the less.
8. One shape per character. Before settling a shape, set it beside the characters it could be mistaken for and look at 13 px.
9. Use the shared parts and symmetries in `parts.py` (`vstem`, `hbar`, `ring`, `arch`, `bowl`, `elbow`, `diag`, `vee`, `cut`, `mirror`, `flip`, `turn`). If a group needs a new part, define it in the group's module; it moves to `parts.py` when a second module needs it.

## Looking

Shapes are judged by eye, on proofs, at every master. From `rachis/`:

```sh
uv run rachis proof --outline a g s -o /tmp/x.png                 # large, with points, handles and metric lines
uv run rachis proof --outline a g s --masters -o /tmp/x.png       # the same for all six masters, stacked
uv run rachis proof --text "hamburgefonstiv" "0O 1lI|" -o /tmp/x.png --sizes 64 16 13
uv run rachis proof --text "..." --masters -o /tmp/x.png          # every master, labelled
RACHIS_REFS=<dir of reference fonts> uv run rachis proof --compare --text "..." -o /tmp/x.png
uv run rachis proof --draft my_module.py --outline a -o /tmp/x.png  # a module outside the package; its glyphs win
uv run rachis check [names...]                                    # builds every master; compares their structure
```

Sizes of 24 px and below are enlarged three times by pixel replication, so the picture shows the pixels a reader gets. Look at the outline sheet for construction (points, joins, overshoot against the lines), at 64 px and more for shape, and at 13 to 16 px for colour: whether the glyph is as dark as its neighbours, whether its counters stay open, whether it could be read as another character.

What to look for:

- Weight. Stems as thick as the stems beside them; no dark knots where strokes meet; curves not thinner than stems at their sides.
- Rhythm. In a line of text the black and the white alternate evenly. A glyph that looks pushed to one side, or leaves a hole beside it, needs its position or width changed.
- Joins. No notch, spike or sliver where strokes overlap; the thin end of an arch hidden inside its stem.
- Curves. No flat spots, kinks or bulges; an S whose spine is as heavy as the stems and whose two halves balance (the lower one slightly larger).
- The Bold. Counters still open; nothing clogged. The Light: nothing spindly or detached.
- The Italic. Slant comes from the kernel; check that nothing leaves the cell on the right and that joins survive.
