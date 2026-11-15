"""Measurements: the numbers behind the design's claims, computed from font files.

Two kinds. ``proportions`` reads a font's outlines: x-height, stem, counters and the ratios legibility research
states its findings in. ``distance`` estimates how alike two characters look at reading size: each is rendered in
its cell, low-pass filtered to what an eye resolves at that size, and the two images are compared.

The distance is a screening tool. It ranks pairs and compares typefaces under one viewing model; it does not
predict how often a person misreads a character. ``docs/measurements.md`` says what it was checked against.
"""

from __future__ import annotations

import contextlib
import math
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from fontTools.pens.basePen import BasePen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from PIL import Image, ImageDraw, ImageFont

# Characters that code confuses, as pairs. The first group is the classic set; the rest are near neighbours.
_WATCHED = "0O 0o 08 0D OD OQ 1l 1I lI l| I| 1| 17 il ij !| 8B 5S 2Z 6b 6G 9g 9q gq ce co eo ao nh hb nu uv vy tf"
_WATCHED_SIGNS = "., :; '` '\" ({ ([ {[ -_ -~"
WATCHED: tuple[tuple[str, str], ...] = tuple((w[0], w[1]) for w in f"{_WATCHED} {_WATCHED_SIGNS}".split(" "))
ALPHANUMERIC = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"


def load_font(path: str | Path, wght: float = 400.0) -> TTFont:
    """A font file, with a variable font pinned to ``wght``."""
    font = TTFont(str(path))
    if "fvar" in font:
        axes = {a.axisTag: a for a in font["fvar"].axes}
        location = {tag: (wght if tag == "wght" else a.defaultValue) for tag, a in axes.items()}
        font = instantiateVariableFont(font, location)
    return font


# ---------------------------------------------------------------------------------------------------------------
# proportions


class _Flatten(BasePen):
    def __init__(self, glyph_set: object) -> None:
        super().__init__(glyph_set)
        self.polygons: list[list[tuple[float, float]]] = []
        self._current: list[tuple[float, float]] = []

    def _moveTo(self, pt: tuple[float, float]) -> None:
        self._current = [pt]

    def _lineTo(self, pt: tuple[float, float]) -> None:
        self._current.append(pt)

    def _curveToOne(self, pt1: tuple[float, float], pt2: tuple[float, float], pt3: tuple[float, float]) -> None:
        a, b, c = pt1, pt2, pt3
        p0 = self._current[-1]
        for i in range(1, 25):
            t = i / 24
            u = 1 - t
            self._current.append(
                (
                    u**3 * p0[0] + 3 * u * u * t * a[0] + 3 * u * t * t * b[0] + t**3 * c[0],
                    u**3 * p0[1] + 3 * u * u * t * a[1] + 3 * u * t * t * b[1] + t**3 * c[1],
                )
            )

    def _qCurveToOne(self, pt1: tuple[float, float], pt2: tuple[float, float]) -> None:
        a, c = pt1, pt2
        p0 = self._current[-1]
        for i in range(1, 25):
            t = i / 24
            u = 1 - t
            self._current.append(
                (u * u * p0[0] + 2 * u * t * a[0] + t * t * c[0], u * u * p0[1] + 2 * u * t * a[1] + t * t * c[1])
            )

    def _closePath(self) -> None:
        self.polygons.append(self._current)
        self._current = []

    def _endPath(self) -> None:
        self._closePath()


def _cmap(font: TTFont) -> dict[int, str]:
    cmap = font.getBestCmap()
    if cmap is None:
        raise ValueError("the font has no Unicode character map")
    return cmap


def _polygons(font: TTFont, char: str) -> list[list[tuple[float, float]]]:
    glyph_set = font.getGlyphSet()
    pen = _Flatten(glyph_set)
    glyph_set[_cmap(font)[ord(char)]].draw(pen)
    return pen.polygons


def _crossings(
    polygons: list[list[tuple[float, float]]], *, y: float | None = None, x: float | None = None
) -> list[float]:
    out: list[float] = []
    for poly in polygons:
        for (x0, y0), (x1, y1) in zip(poly, [*poly[1:], poly[0]], strict=True):
            if y is not None and (y0 - y) * (y1 - y) < 0:
                out.append(x0 + (x1 - x0) * (y - y0) / (y1 - y0))
            if x is not None and (x0 - x) * (x1 - x) < 0:
                out.append(y0 + (y1 - y0) * (x - x0) / (x1 - x0))
    return sorted(out)


def _bounds(polygons: list[list[tuple[float, float]]]) -> tuple[float, float, float, float]:
    xs = [q[0] for poly in polygons for q in poly]
    ys = [q[1] for poly in polygons for q in poly]
    return min(xs), min(ys), max(xs), max(ys)


@dataclass(frozen=True, slots=True)
class Proportions:
    """A font's proportions in thousandths of the em, and the ratios research uses."""

    advance: float
    x_height: float
    cap_height: float
    ascender: float
    descender: float
    stem: float  # vertical stem of n
    hair: float  # horizontal bar of H
    n_counter: float
    n_gap: float  # the white between two n's: n's two side bearings
    zero_width: float
    o_cap_width: float
    period: float

    @property
    def stem_to_x_height(self) -> float:
        return self.stem / self.x_height

    @property
    def stem_to_hair(self) -> float:
        return self.stem / self.hair

    @property
    def advance_to_x_height(self) -> float:
        return self.advance / self.x_height

    @property
    def counter_to_x_height(self) -> float:
        return self.n_counter / self.x_height

    @property
    def gap_to_counter(self) -> float:
        return self.n_gap / self.n_counter

    @property
    def zero_to_o(self) -> float:
        return self.zero_width / self.o_cap_width


def proportions(font: TTFont) -> Proportions:
    k = 1000.0 / font["head"].unitsPerEm  # ty: ignore[missing-attribute]
    cmap = _cmap(font)
    advance = font["hmtx"][cmap[ord("n")]][0]

    def box(ch: str) -> tuple[float, float, float, float]:
        return _bounds(_polygons(font, ch))

    xh = box("x")[3]
    cap = box("H")[3]
    n = _crossings(_polygons(font, "n"), y=xh * 0.25 + 0.37)
    h_bar = _crossings(_polygons(font, "H"), x=advance / 2 + 0.37)
    zero, o_cap, dot = box("0"), box("O"), box(".")
    return Proportions(
        advance=advance * k,
        x_height=xh * k,
        cap_height=cap * k,
        ascender=box("b")[3] * k,
        descender=box("p")[1] * k,
        stem=(n[1] - n[0]) * k,
        hair=(h_bar[1] - h_bar[0]) * k,
        n_counter=(n[2] - n[1]) * k,
        n_gap=(n[0] + advance - n[3]) * k,
        zero_width=(zero[2] - zero[0]) * k,
        o_cap_width=(o_cap[2] - o_cap[0]) * k,
        period=(dot[2] - dot[0]) * k,
    )


# ---------------------------------------------------------------------------------------------------------------
# how alike two characters look


@dataclass(frozen=True, slots=True)
class Viewing:
    """A viewing condition. ``px`` is the font size in pixels per em and ``sigma`` the standard deviation, in
    pixels, of the Gaussian that stands for the eye's blur. At 14 px the eye's optics give about 0.6 px on an
    ordinary display at an ordinary distance; 1.0 px is where the detail that reading uses runs out; 1.5 px
    stands for dark themes, defocus and a glance."""

    px: float = 14.0
    sigma: float = 1.0
    supersample: int = 8


class Renderer:
    """Renders characters of one font in their cells, filtered for a viewing condition."""

    def __init__(self, path: str | Path, view: Viewing, wght: float = 400.0) -> None:
        self.view = view
        size = round(view.px * view.supersample)
        self._font = ImageFont.truetype(str(path), size)
        with contextlib.suppress(OSError):  # a static font has no axes
            self._font.set_variation_by_axes([wght])
        self._size = size
        self._cache: dict[str, np.ndarray] = {}
        self._kernel = _gaussian(view.sigma * view.supersample)
        self._box = np.ones(view.supersample) / view.supersample

    def image(self, char: str) -> np.ndarray:
        """The filtered image of ``char`` in a cell 0.6 em wide (a wider glyph keeps its own advance) and 1.6 em
        tall, with the baseline at a fixed height."""
        if char not in self._cache:
            width = max(round(self._font.getlength(char)), round(0.6 * self._size))
            pad = 3 * self.view.supersample
            canvas = Image.new("L", (width + 2 * pad, round(1.6 * self._size)), 0)
            ImageDraw.Draw(canvas).text((pad, round(1.15 * self._size)), char, font=self._font, fill=255, anchor="ls")
            a = np.asarray(canvas, dtype=np.float64) / 255.0
            for kernel in (self._box, self._kernel):  # the pixel's aperture, then the eye
                a = _convolve(a, kernel)
            self._cache[char] = a
        return self._cache[char]

    def distance(self, a: str, b: str, shift: bool = True) -> float:
        """0 when the two filtered images are identical, sqrt(2) when they share no ink. With ``shift``, the
        smallest value over displacements of up to one pixel either way, since a reader does not know where a
        character sits to the pixel."""
        ia, ib = self.image(a), self.image(b)
        if ia.shape != ib.shape:
            w = max(ia.shape[1], ib.shape[1])
            ia = np.pad(ia, ((0, 0), (0, w - ia.shape[1])))
            ib = np.pad(ib, ((0, 0), (0, w - ib.shape[1])))
        norm = math.sqrt((float((ia**2).sum()) + float((ib**2).sum())) / 2.0)
        if norm == 0.0:
            return 0.0
        steps = (0,)
        if shift:
            half = self.view.supersample // 2
            steps = (-2 * half, -half, 0, half, 2 * half)
        best = math.inf
        for dx in steps:
            for dy in steps:
                moved = np.roll(np.roll(ib, dx, axis=1), dy, axis=0)
                best = min(best, float(np.sqrt(((ia - moved) ** 2).sum())) / norm)
        return best


def _gaussian(sigma: float) -> np.ndarray:
    if sigma <= 0:
        return np.ones(1)
    radius = max(1, math.ceil(3.5 * sigma))
    x = np.arange(-radius, radius + 1)
    k = np.exp(-(x**2) / (2 * sigma**2))
    return k / k.sum()


def _convolve(a: np.ndarray, kernel: np.ndarray) -> np.ndarray:
    a = np.apply_along_axis(lambda row: np.convolve(row, kernel, mode="same"), 1, a)
    return np.apply_along_axis(lambda col: np.convolve(col, kernel, mode="same"), 0, a)


def pair_distances(
    path: str | Path, pairs: Iterable[tuple[str, str]], view: Viewing, wght: float = 400.0
) -> dict[tuple[str, str], float]:
    r = Renderer(path, view, wght)
    return {(a, b): r.distance(a, b) for a, b in pairs}


def all_pairs(
    path: str | Path, chars: Sequence[str], view: Viewing, wght: float = 400.0
) -> list[tuple[float, str, str]]:
    """Every unordered pair of ``chars`` with its distance, closest first."""
    r = Renderer(path, view, wght)
    out = [(r.distance(a, b), a, b) for i, a in enumerate(chars) for b in chars[i + 1 :]]
    return sorted(out)
