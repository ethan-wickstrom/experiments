# Drawing

How a glyph is written and judged. `design.md` says what the shapes are; this is the method.

## The model

A glyph is a function, a glyph program, that draws on a canvas (`Draw`) for one master (`Params`). The kernel is METAFONT's model in Rust:

- A stroke is a list of knots. `knot(x, y, w)` is a point of the skeleton and the breadth of the pen there. `.pen(deg)` fixes the pen's angle (otherwise it is square to the path), `.dir(deg)` the direction of travel, `.line()` makes the piece to the next knot straight, `.k(p.sq)` makes the corner to the next knot a superellipse quadrant, `.tension(a, b)` sets Hobby's tensions.
- The centre line through the knots is Hobby's spline (the curve METAFONT draws through points), or the superellipse where a knot asks for it. The outline is the centre line offset to both sides by half the pen, so a round stroke keeps its breadth around a turn. Each stroke is a closed contour of its own; strokes overlap, and that is kept in the variable fonts (it is what lets the masters interpolate) and removed in the static ones.
- An italic shears the skeleton and leaves the pen as it is, so stems keep their thickness.

```rust
fn n(g: &mut Draw) {
    let p = g.p;
    g.stroke(&vstem(p.xl(), 0.0, p.xh, p.stem));
    g.stroke(&arch(p, p.xl(), p.xr(), p.xh + p.over, 0.0, Arch::default()));
}
```

`p` holds every measurement a program may read: heights (`xh`, `cap`, `asc`, `desc`, `over`), strokes (`stem`, `hair`, `cap_stem`, `cap_hair`, `op`), spacing (`sb`, `sb_round`, `cap_sb`, `fig_sb`, `counter`), the operators' axis and span (`axis`, `op_l`, `op_r()`), the line box (`line_top`, `line_bot`), and the cell: `p.width` is the width of the cell this glyph is drawn into, `p.mid()` its middle, `p.xl()` and `p.xr()` the centre lines of its two standard stems. Shared skeleton parts are in `crates/glyphs/src/parts.rs` (`vstem`, `hbar`, `ring`, `arch`, `bowl`, `elbow`, `diag`, `vee`, `cut`, `mirror`, `flip`, `turn`).

A program can look at other glyphs: `g.glyph_of_char('a')` gives the finished glyph of its master (contours, bounds, advance, anchors); `g.glyph_as(name, &other)` and `g.draw_as(name, &other, dx, dy)` build or draw a glyph as another parameter set would, which is how small letters are made (`p.scaled(0.56)` with strokes of its own); `g.same_as_char(c)` makes one glyph another under a second code point.

A module ends with `pub fn register(reg: &mut Registry)`, which names its glyphs: `reg.ch('n', n)`, `reg.named("zero.dot", zero_dot)`, `reg.ch_with('─', Opt::UPRIGHT, line)`, `Opt::MARK` for a combining mark.

## Rules

- Never branch on weight or optical size, and never draw a different number of contours, segments or components in different masters of a face: the variable font interpolates them point by point. What varies is arithmetic on `p`, and a size must not pass through zero between the Light and the Bold (a counter that closes comes out turned round). `rachis check` compares the structure of every glyph across the masters of each face and reports a contour that has no shape half-way between two of them.
- Branching on `p.mono` and on `p.italic()` is allowed: every master of a face has the same pitch and the same slant.
- Never write 600 or 300: write `p.width` and `p.mid()`. A program must draw correctly in any cell it is given.
- Letters use `p.stem` and `p.hair`; capitals `p.cap_stem` and `p.cap_hair`; signs and arrows `p.op`, and `fine(p)` for a stroke inside another shape. Round shapes overshoot flat ones by `p.over`.
- In the proportional family a letter's width is not in its program. The module's `ask(name, p)` states the sidebearings and the ink (`around(left, ink, right)`, `beside(left, right)` for a shape of fixed size), and the build measures the program to find the cell (`crates/glyphs/src/text.rs`). Figures and the signs of arithmetic keep the master's cell. Every other sign has a room in `crates/glyphs/src/signs.rs` (its span and its margins, T27): its program is not changed for it, and must draw across the cell it is given. A measure that should grow with the span multiplies by `p.grown`; one that a whole kind shares (the height of a turnstile) grows up to that kind's span and no further (`relation_growth`, `round_growth` in `operators.rs`). A sign built on another sign as a component centres what it adds on `middle_of(g, c)`, not on `p.mid()`: the component stands where its own room put it.
- A number quoted in a document comes from a command that can be rerun.

## Looking

Shapes are judged by eye on proofs, at every master, large and at 13 to 16 px, beside the characters they could be mistaken for.

```sh
cargo run -q -p rachis -- check                         # structure across masters: must end "0 problems"
cargo run -q -p rachis -- proof --outline a b c -o x.png --master "Mono Regular" --em 420
cargo run -q -p rachis -- proof --outline a -o a.png --skeleton
cargo run -q -p rachis -- proof --text "line one" "line two" -o t.png --sizes 40 16 13 --master "Text Regular"
cargo run -q -p rachis -- proof --text "..." -o t.png --masters
RACHIS_REFS=<directory of reference fonts> cargo run -q -p rachis -- proof --text "..." -o c.png --compare
cargo run -q -p rachis -- widths --master "Text Regular" "nobdpq"   # advance, sidebearings, ink
cargo run -q -p rachis -- kern --master "Text Regular" To AV "r."   # the kerning the fonts carry; --own: the master's own
cargo run -q -p rachis -- measure --refs <directory of reference fonts> --out docs/measurements.md
```

Master names: `Mono Light`, `Mono Regular`, `Mono Bold` and their italics (`Mono Italic`, `Mono Bold Italic`); `Text Light`, `Text Regular`, `Text Bold`; `Small Light`, `Small Regular`, `Small Bold`; and the italics of those. Text proofs set a fixed-pitch master on a terminal's grid (integer cells and baselines) and a proportional one as a browser does, with its kerning.

What to look for: stroke weight that does not match the neighbours; lumpy or flat-spotted curves; kinks at joins; counters that clog in the Bold or look empty in the Light; strokes that collide; shapes that sit too high, low, left or right; ends cut at inconsistent angles; anything that reads as another character at 13 px. Then the italic: nothing may leave its cell or collide.

After a change that should not move outlines, `cargo run -q -p rachis -- digest --check` compares every module of every master with the snapshot in `tests/snapshot/outlines.sha256`; after one that should, `digest --write` renews it, and `digest --glyphs` before and after shows which glyphs moved.
