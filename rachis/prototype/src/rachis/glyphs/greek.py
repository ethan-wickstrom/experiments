"""Greek, and the letters mathematics borrows: variant Greek forms, double-struck capitals, ℓ, ℏ, ℵ.

The Greek is the Latin's typeface: the same strokes, heights and superellipse. A capital that has the shape of a
Latin capital is that glyph as a component. Letters with three vertical strokes in the cell (Φ Ψ φ ψ ω) take the
thinner stroke of ``_three``, as m and w do.
"""

from __future__ import annotations

from rachis.geom import pt, unit
from rachis.glyph import Draw, Knot, char
from rachis.params import Params
from rachis.parts import arch, bowl, cut, diag, elbow, hbar, mirror, ring, turn, vee, vstem

# -- measurements this group derives from the parameters -------------------------------------------------------


def _cap_round(p: Params) -> tuple[float, float, float, float]:
    """The box of the Latin O, which Θ, Ω and the double-struck rounds share."""
    x0 = p.sb_round - 8
    return x0, -p.over, p.width - x0, p.cap + p.over


def _cap_three(p: Params) -> float:
    """The stroke of a capital that puts three verticals in the cell (Φ, Ψ)."""
    return 0.5 * (p.cap_stem + p.cap_hair)


# -- capitals that are Latin capitals ---------------------------------------------------------------------------

for _greek, _latin in zip("ΑΒΕΖΗΙΚΜΝΟΡΤΥΧ", "ABEZHIKMNOPTYX", strict=True):

    def _same(g: Draw, latin: str = _latin) -> None:
        g.use(latin)

    char(_greek)(_same)


# -- capitals ---------------------------------------------------------------------------------------------------


@char("Γ")
def Gamma(g: Draw) -> None:
    p = g.p
    x = p.cxl + 30
    g.stroke(*vstem(x, 0, p.cap, p.cap_stem))
    g.stroke(*hbar(x, p.width - p.sb_round - 10, p.cap - p.cap_hair / 2, p.cap_hair))


def _caret(p: Params) -> tuple[float, float, float, float]:
    """Outer feet, stroke and apex of Λ and Δ: the Latin A's."""
    t = p.cap_stem * 0.96
    return p.sb_round - 34, p.width - p.sb_round + 34, t, t * 0.92


@char("Δ")
def Delta(g: Draw) -> None:
    p = g.p
    x0, x1, t, apex = _caret(p)
    g.poly(vee(x0, x1, 0, p.cap, t, apex))
    inset = (p.mid - apex / 2 - x0) * p.cap_hair / p.cap  # where the outer edge is at the bar's top
    g.stroke(*hbar(x0 + inset, x1 - inset, p.cap_hair / 2, p.cap_hair))


@char("Λ")
def Lambda(g: Draw) -> None:
    p = g.p
    x0, x1, t, apex = _caret(p)
    g.poly(vee(x0, x1, 0, p.cap, t, apex))


@char("Θ")
def Theta(g: Draw) -> None:
    p = g.p
    x0, y0, x1, y1 = _cap_round(p)
    g.stroke(*ring(x0, y0, x1, y1, p.cap_stem, p.cap_hair, p.sq + 0.02), closed=True)
    half = 0.27 * (x1 - x0 - 2 * p.cap_stem)  # the bar floats: a gap of 0.23 of the counter on each side
    g.stroke(*hbar(p.mid - half, p.mid + half, p.cap / 2, p.cap_hair))


@char("Ξ")
def Xi(g: Draw) -> None:
    p = g.p
    x0, x1 = p.sb_round + 10, p.width - p.sb_round - 10
    h = p.cap_hair
    g.stroke(*hbar(x0, x1, p.cap - h / 2, h))
    g.stroke(*hbar(x0 + 62, x1 - 62, p.cap / 2, h))
    g.stroke(*hbar(x0, x1, h / 2, h))


@char("Π")
def Pi(g: Draw) -> None:
    p = g.p
    g.stroke(*vstem(p.cxl, 0, p.cap, p.cap_stem))
    g.stroke(*vstem(p.cxr, 0, p.cap, p.cap_stem))
    g.stroke(*hbar(p.cxl - p.cap_stem / 2, p.cxr + p.cap_stem / 2, p.cap - p.cap_hair / 2, p.cap_hair))


@char("Σ")
def Sigma(g: Draw) -> None:
    p = g.p
    x0, x1 = p.sb_round + 16, p.width - p.sb_round - 16
    h, t = p.cap_hair, p.cap_stem * 0.96
    xv = p.mid - 26  # the centre line's vertex; the mitre's point lies half a stroke further right
    xa = x0 + t / 2
    for _ in range(3):  # the diagonal's left edge starts on x0
        xa = x0 + diag(xa, p.cap, xv, p.cap / 2, t)[0].w / 2
    w = diag(xa, p.cap, xv, p.cap / 2, t)[0].w
    g.stroke(Knot(pt(xa, p.cap), w, pen=0, line=True), Knot(pt(xv, p.cap / 2), t, line=True), Knot(pt(xa, 0), w, pen=0))
    g.stroke(*hbar(xa, x1, p.cap - h / 2, h))
    g.stroke(*hbar(xa, x1 + 4, h / 2, h))


@char("Φ")
def Phi(g: Draw) -> None:
    p = g.p
    t = _cap_three(p)
    x0 = p.sb_round - 24
    g.stroke(*ring(x0, p.cap * 0.14, p.width - x0, p.cap * 0.86, t, p.cap_hair * 0.94, p.sq + 0.02), closed=True)
    g.stroke(*vstem(p.mid, 0, p.cap, t))


@char("Ψ")
def Psi(g: Draw) -> None:
    p = g.p
    t = _cap_three(p)
    h = p.cap_hair * 0.94
    xa = p.sb_round - 22 + t / 2
    bottom = p.cap * 0.27
    turn_ = p.cap * 0.56
    g.stroke(
        Knot(pt(xa, p.cap), t, pen=0, line=True),
        Knot(pt(xa, turn_), t, pen=0, dir=-90, k=p.sq),
        Knot(pt(p.mid, bottom + h / 2), h, dir=0, k=p.sq),
        Knot(pt(p.width - xa, turn_), t, pen=0, dir=90, line=True),
        Knot(pt(p.width - xa, p.cap), t, pen=0),
    )
    g.stroke(*vstem(p.mid, 0, p.cap, t))


@char("Ω")
def Omega(g: Draw) -> None:
    p = g.p
    x0, _, x1, y1 = _cap_round(p)
    s, h = p.cap_stem, p.cap_hair
    lean = 58.0  # the direction, from the horizontal, in which the ring comes down onto its feet
    end = cut(0, h * 0.5, s, -180 + lean, pen=0)
    gap = 0.17 * (x1 - x0 - 2 * s)  # half the opening between the ring's two ends
    xn = p.mid - gap - end.w / 2
    side = p.cap * 0.52
    g.stroke(
        cut(xn, h * 0.5, s, 180 - lean, pen=0),
        Knot(pt(x0 + s / 2, side), s, dir=90, k=p.sq + 0.02),
        Knot(pt(p.mid, y1 - h / 2), h, dir=0, k=p.sq + 0.02),
        Knot(pt(x1 - s / 2, side), s, dir=-90),
        cut(p.width - xn, h * 0.5, s, -180 + lean, pen=0),
    )
    foot = xn + end.w / 2 + 4
    g.stroke(*hbar(x0 - 6, foot, h / 2, h))
    g.stroke(*hbar(p.width - foot, x1 + 6, h / 2, h))


@char("\u2126")  # the ohm sign
def ohm(g: Draw) -> None:
    g.use("\u03a9")


# -- lowercase --------------------------------------------------------------------------------------------------


@char("ο")
def omicron(g: Draw) -> None:
    g.use("o")


@char("α")
def alpha(g: Draw) -> None:
    p = g.p
    xs = p.xr - 36  # the stem stands left of d's, and its foot takes the room
    g.stroke(*mirror(bowl(p, p.width - xs, p.width - p.sb_round + 6, -p.over, p.xh + p.over), p.mid))
    g.stroke(*elbow(xs, p.xh, 0, p.width - p.sb_round + 22, p.stem, p.hair, p.sq, 84))


@char("β")
def beta(g: Draw) -> None:
    p = g.p
    xs = p.xl + 2
    s, h = p.stem, p.hair
    top, bot = p.asc + p.over - h / 2, -p.over + h / 2
    waist = p.asc * 0.56
    edge_hi, edge_lo = p.width - p.sb_round - 40, p.width - p.sb_round - 4
    inner = xs + s / 2
    xa = inner + 0.46 * (edge_hi - s - inner)
    bar = inner + 0.30 * (edge_hi - s - inner)  # the waist's bar stops short of the stem
    g.stroke(
        Knot(pt(xs, p.desc), s, pen=0, line=True),
        Knot(pt(xs, p.asc - 0.8 * (xa - xs)), s, pen=0, dir=90, k=p.sq),
        Knot(pt(xa, top), h, dir=0, k=p.sq),
        Knot(pt(edge_hi - s * 0.48, (waist + top) / 2), s * 0.96, dir=-90, k=p.sq),
        Knot(pt(xa + 16, waist), h, pen=90, dir=180, line=True),
        Knot(pt(bar, waist), h, pen=90),
    )
    j = p.join * s
    y_end = bot + 0.30 * (waist - bot)
    g.stroke(
        Knot(pt(bar, waist), h, pen=90, line=True),
        Knot(pt(xa + 26, waist), h, pen=90, dir=0, k=p.sq),
        Knot(pt(edge_lo - s / 2, (waist + bot) / 2), s, dir=-90, k=p.sq),
        Knot(pt(inner + 0.5 * (edge_lo - s - inner), bot), h, dir=180),
        Knot(pt(inner - 3, y_end) + (j / 2) * unit(122) * 1j, j, dir=122),
    )


@char("γ")
def gamma(g: Draw) -> None:
    p = g.p
    t = p.stem * 0.94
    yv = p.xh * 0.13
    g.poly(vee(p.sb_round + 6, p.width - p.sb_round - 6, p.xh, yv, t, p.stem * 0.9))
    g.stroke(*vstem(p.mid, p.desc, yv + p.stem * 0.6, p.stem))


@char("δ")
def delta(g: Draw) -> None:
    p = g.p
    s, h = p.stem, p.hair
    x0, x1 = p.sb_round + 8, p.width - p.sb_round - 8
    cx = (x0 + x1) / 2
    y0, y1 = -p.over, p.xh * 0.86
    g.stroke(*ring(x0, y0, x1, y1, s, h, p.sq), closed=True)
    rx, ry = (x1 - x0 - s) / 2, (y1 - y0 - h) / 2
    g.stroke(
        cut(x1 - 40, p.asc - 78, h * 1.04, 148),
        Knot(pt(cx + 6, p.asc + p.over - h / 2), h, dir=180, k=p.sq),
        Knot(pt(x0 + 74 + s / 2, p.asc - 128), s * 0.9, dir=-82),
        Knot(pt(cx + 0.70 * rx, (y0 + y1) / 2 + 0.80 * ry), (s + h) / 2, dir=-42),
    )


@char("ε")
def epsilon(g: Draw) -> None:
    p = g.p
    s, h = p.stem, p.hair
    x0, x1 = p.sb_round + 22, p.width - p.sb_round - 22
    cx = (x0 + x1) / 2
    top, bot = p.xh + p.over - h / 2, -p.over + h / 2
    waist = p.xh * 0.52
    tongue = cx + 30
    g.stroke(
        cut(x1 - 10, p.xh - 108, h * 1.04, 144),
        Knot(pt(cx + 6, top), h, dir=180, k=p.sq),
        Knot(pt(x0 + 22 + s / 2, (top + waist) / 2), s * 0.96, dir=-90, k=p.sq),
        Knot(pt(cx - 30, waist), h, pen=90, dir=0, line=True),
        Knot(pt(tongue, waist), h, pen=90),
    )
    g.stroke(
        Knot(pt(tongue, waist), h, pen=90, line=True),
        Knot(pt(cx - 34, waist), h, pen=90, dir=180, k=p.sq),
        Knot(pt(x0 + s / 2, (waist + bot) / 2), s, dir=-90, k=p.sq),
        Knot(pt(cx + 4, bot), h, dir=0),
        cut(x1, 106, h * 1.04, 36),
    )


def _tail(p: Params, x: float, y: float) -> list[Knot]:
    """The end of ζ, ξ and ς: a bar travelling right at height ``y`` turns down at ``x`` and stops, cut flat,
    below the baseline."""
    r = 0.9 * p.stem
    return [
        Knot(pt(x - r, y), p.hair, dir=0, k=p.sq),
        Knot(pt(x, y - r), p.stem * 0.92, pen=0, dir=-90),
        cut(x - 18, p.desc * 0.82, p.stem * 0.84, -104, pen=0),
    ]


@char("ζ")
def zeta(g: Draw) -> None:
    p = g.p
    s, h = p.stem, p.hair
    x0, x1 = p.sb_round + 26, p.width - p.sb_round - 26
    g.stroke(*hbar(x0, x1, p.asc - h / 2, h))
    yb = h / 2
    g.stroke(
        cut(x1 - 52, p.asc - h / 2, h * 1.06, -128, pen=0),
        Knot(pt(x0 + 14 + s / 2, p.asc * 0.34), s, dir=-90, k=p.sq),
        Knot(pt(p.mid - 10, yb), h, dir=0, line=True),
        *_tail(p, x1 - 20 - s / 2, yb),
    )


@char("ξ")
def xi(g: Draw) -> None:
    p = g.p
    s, h = p.stem, p.hair
    x0, x1 = p.sb_round + 26, p.width - p.sb_round - 26
    yt, yb = p.asc - h / 2, h / 2
    waist = p.asc * 0.58
    cx = p.mid
    tongue = x1 - 62
    g.stroke(
        Knot(pt(x1 - 14, yt), h, pen=90, line=True),
        Knot(pt(cx, yt), h, pen=90, dir=180, k=p.sq),
        Knot(pt(x0 + 36 + s / 2, (yt + waist) / 2), s * 0.96, dir=-90, k=p.sq),
        Knot(pt(cx, waist), h, pen=90, dir=0, line=True),
        Knot(pt(tongue, waist), h, pen=90),
    )
    g.stroke(
        Knot(pt(tongue, waist), h, pen=90, line=True),
        Knot(pt(cx - 10, waist), h, pen=90, dir=180, k=p.sq),
        Knot(pt(x0 + s / 2, (waist + yb) / 2), s, dir=-90, k=p.sq),
        Knot(pt(cx - 10, yb), h, dir=0, line=True),
        *_tail(p, x1 - 20 - s / 2, yb),
    )


@char("η")
def eta(g: Draw) -> None:
    p = g.p
    g.stroke(*vstem(p.xl, 0, p.xh, p.stem))
    g.stroke(*arch(p, p.xl, p.xr, p.xh + p.over, p.desc))


@char("θ")
def theta(g: Draw) -> None:
    p = g.p
    x0 = p.sb_round + 36
    g.stroke(*ring(x0, -p.over, p.width - x0, p.asc + p.over, p.stem, p.hair, p.sq), closed=True)
    g.stroke(*hbar(x0 + p.stem / 2, p.width - x0 - p.stem / 2, p.asc / 2, p.hair * 0.94))


@char("ι")
def iota(g: Draw) -> None:
    p = g.p
    g.stroke(*elbow(p.mid - 40, p.xh, 0, p.width - p.sb_round - 50, p.stem, p.hair, p.sq, 112))


@char("κ")
def kappa(g: Draw) -> None:
    p = g.p
    x = p.xl + 10
    t = p.stem * 0.94
    xr = p.width - p.sb_round + 2
    g.stroke(*vstem(x, 0, p.xh, p.stem))
    g.stroke(Knot(pt(x, p.xh * 0.34), t, line=True), diag(0, 0, xr - 54, p.xh, t)[1])
    g.stroke(Knot(pt(x + 112, p.xh * 0.52), t, line=True), diag(0, p.xh, xr - 46, 0, t)[1])


@char("λ")
def lambda_(g: Draw) -> None:
    p = g.p
    t = p.stem * 0.96
    xa, xb = p.sb_round + 84, p.width - p.sb_round - 28  # the long stroke's centre line, top and bottom
    xc = p.sb_round + 40  # the leg's foot
    yj = p.xh * 0.72
    xj = xa + (xb - xa) * (p.asc - yj) / p.asc
    g.stroke(*diag(xa, p.asc, xb, 0, t))
    g.stroke(Knot(pt(xj, yj), t, line=True), diag(xj, yj, xc, 0, t)[1])


@char("μ")
def mu(g: Draw) -> None:
    p = g.p
    g.stroke(*vstem(p.xl, p.desc, p.xh, p.stem))
    g.stroke(*vstem(p.xr, 0, p.xh, p.stem))
    g.stroke(*turn(arch(p, p.xl, p.xr, p.xh + p.over, 0), p.mid, p.xh / 2))


@char("µ")  # the micro sign
def micro(g: Draw) -> None:
    g.use("μ")
