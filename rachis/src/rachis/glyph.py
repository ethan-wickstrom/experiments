"""Glyphs, the registry of glyph programs, and the canvas a program draws on.

A glyph program is a function that takes a ``Draw`` and adds strokes and shapes to it. It reads every measurement
from ``Draw.p``, the parameters of the master being drawn, and it must not branch on them: the same program has to
produce the same structure for every master, because the variable font interpolates between them.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, field

from rachis.geom import segment_bounds
from rachis.names import name_of
from rachis.params import Params
from rachis.pen import Contour, Knot, expand, polygon, rect, sheared, superellipse


@dataclass(slots=True)
class Glyph:
    name: str
    advance: float
    unicodes: tuple[int, ...] = ()
    contours: list[Contour] = field(default_factory=list)
    components: list[tuple[str, complex]] = field(default_factory=list)
    anchors: dict[str, complex] = field(default_factory=dict)
    mark: bool = False
    # the strokes the outline came from, as drawn (knots, closed): for diagrams, not for the font
    skeletons: list[tuple[tuple[Knot, ...], bool]] = field(default_factory=list)

    def bounds(self) -> tuple[float, float, float, float] | None:
        segs = [s for c in self.contours for s in c.segs]
        return segment_bounds(segs) if segs else None

    def signature(self) -> str:
        parts = [c.signature() for c in self.contours]
        parts.extend(f"@{name}" for name, _ in self.components)
        parts.extend(f"#{name}" for name in sorted(self.anchors))
        return " ".join(parts)


class Draw:
    """The canvas of one glyph in one master."""

    def __init__(self, p: Params, name: str, advance: float, upright: bool = False) -> None:
        self.p = p
        self.glyph = Glyph(name, advance)
        self._slope = 0.0 if upright else math.tan(math.radians(p.slant))

    # -- coordinates ------------------------------------------------------------------------------------------

    def _shear_point(self, z: complex) -> complex:
        return complex(z.real + self._slope * (z.imag - self.p.slant_origin), z.imag)

    # -- strokes ----------------------------------------------------------------------------------------------

    def stroke(self, *knots: Knot, closed: bool = False) -> None:
        """Add the outline of the stroke through ``knots``."""
        ks = [sheared(k, self._slope, self.p.slant_origin) for k in knots]
        self.glyph.contours.extend(expand(ks, closed))
        self.glyph.skeletons.append((tuple(ks), closed))

    # -- filled shapes ----------------------------------------------------------------------------------------

    def add(self, contour: Contour, slant: bool = True) -> None:
        self.glyph.contours.append(contour.mapped(self._shear_point) if slant and self._slope else contour)

    def rect(self, x0: float, y0: float, x1: float, y1: float, slant: bool = True) -> None:
        self.add(rect(x0, y0, x1, y1), slant)

    def poly(self, points: Sequence[complex | tuple[float, float]], slant: bool = True) -> None:
        self.add(polygon([complex(*q) if isinstance(q, tuple) else q for q in points]), slant)

    def dot(self, cx: float, cy: float, rx: float, ry: float | None = None, k: float | None = None) -> None:
        """A round dot. An italic moves it along the slant but does not shear it."""
        c = self._shear_point(complex(cx, cy))
        self.glyph.contours.append(
            superellipse(c.real, c.imag, rx, rx if ry is None else ry, self.p.dot_k if k is None else k)
        )

    # -- composition ------------------------------------------------------------------------------------------

    def use(self, name: str, dx: float = 0.0, dy: float = 0.0) -> None:
        """Place another glyph as a component, moved by (dx, dy) in upright coordinates. ``name`` is a glyph name,
        or a single character, which stands for its canonical name."""
        if len(name) == 1:
            name = name_of(name)
        self.glyph.components.append((name, complex(dx + self._slope * dy, dy)))

    def anchor(self, name: str, x: float, y: float) -> None:
        self.glyph.anchors[name] = self._shear_point(complex(x, y))


Program = Callable[[Draw], None]


@dataclass(frozen=True, slots=True)
class Spec:
    name: str
    unicodes: tuple[int, ...]
    program: Program
    advance: float | None
    upright: bool
    mark: bool
    module: str


REGISTRY: dict[str, Spec] = {}
REPLACING: bool = False  # set while a draft module loads: its glyphs may replace registered ones


def glyph(
    name: str,
    *unicodes: int | str,
    advance: float | None = None,
    upright: bool = False,
    mark: bool = False,
) -> Callable[[Program], Program]:
    """Register a glyph program under a glyph name and the characters it encodes.

    ``upright`` keeps the glyph out of the italic's slant (box drawing, blocks). ``mark`` makes it a combining mark
    with no advance.
    """
    cps = tuple(ord(u) if isinstance(u, str) else u for u in unicodes)

    def register(program: Program) -> Program:
        if name in REGISTRY and not REPLACING:
            raise ValueError(f"glyph {name!r} is defined twice ({REGISTRY[name].module}, {program.__module__})")
        REGISTRY[name] = Spec(name, cps, program, advance, upright, mark, program.__module__)
        return program

    return register


def char(character: str, *, upright: bool = False, mark: bool = False) -> Callable[[Program], Program]:
    """Register a glyph program for one character under its canonical name (``names.name_of``)."""
    return glyph(name_of(character), character, upright=upright, mark=mark)


def build(spec: Spec, p: Params) -> Glyph:
    advance = 0.0 if spec.mark else (p.width if spec.advance is None else spec.advance)
    g = Draw(p, spec.name, advance, spec.upright)
    spec.program(g)
    g.glyph.unicodes = spec.unicodes
    g.glyph.mark = spec.mark
    return g.glyph


def build_all(p: Params, names: Iterable[str] | None = None) -> dict[str, Glyph]:
    """Every registered glyph (or ``names`` and the components they use) drawn for the master ``p``."""
    wanted = list(REGISTRY) if names is None else list(names)
    out: dict[str, Glyph] = {}
    while wanted:
        name = wanted.pop()
        if name in out:
            continue
        if name not in REGISTRY:
            raise KeyError(f"no glyph program named {name!r}")
        out[name] = build(REGISTRY[name], p)
        wanted.extend(base for base, _ in out[name].components)
    return out


__all__ = ["REGISTRY", "Draw", "Glyph", "Knot", "Spec", "build", "build_all", "char", "glyph"]
