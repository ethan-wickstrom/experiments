"""The build: glyph programs to font files.

Each master is drawn, written as a UFO, and described by a designspace (one for the upright, one for the italic).
fontmake compiles each designspace into a variable font and into static instances; this module then finishes
every file (tables fontmake does not set, hinting, web formats) and records the SHA-256 of each in a manifest.

The build is reproducible: timestamps come from ``meta.EPOCH``, so the same source gives the same bytes.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import ufoLib2
from fontTools.designspaceLib import (
    AxisDescriptor,
    AxisLabelDescriptor,
    DesignSpaceDocument,
    InstanceDescriptor,
    SourceDescriptor,
)
from fontTools.otlLib.builder import buildStatTable
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables import _g_l_y_f

from rachis import glyphs as glyph_modules
from rachis import meta
from rachis.features import feature_file
from rachis.geom import Line
from rachis.glyph import REGISTRY, Glyph, build_all
from rachis.params import ITALIC_MASTERS, SLANT, UPRIGHT_MASTERS, Params

ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class Style:
    """A named instance: one of the static fonts, and a named point of a variable font."""

    weight_name: str
    wght: int
    italic: bool

    @property
    def name(self) -> str:
        if not self.italic:
            return self.weight_name
        return "Italic" if self.weight_name == "Regular" else f"{self.weight_name} Italic"

    @property
    def file_stem(self) -> str:
        return f"{meta.FAMILY}-{self.name.replace(' ', '')}"

    @property
    def linked(self) -> bool:
        """Whether this style belongs to the four-member family that applications link (Regular, Italic, Bold,
        Bold Italic). The others are families of their own to software that knows only four styles."""
        return self.weight_name in ("Regular", "Bold")

    @property
    def map_family(self) -> str:
        return meta.FAMILY if self.linked else f"{meta.FAMILY} {self.weight_name}"

    @property
    def map_style(self) -> str:
        bold = self.weight_name == "Bold"
        return {(False, False): "regular", (True, False): "bold", (False, True): "italic", (True, True): "bold italic"}[
            (bold, self.italic)
        ]


STYLES = tuple(Style(name, wght, italic) for italic in (False, True) for name, wght in meta.WEIGHTS)


# ---------------------------------------------------------------------------------------------------------------
# sources


def glyph_order(glyphs: dict[str, Glyph]) -> list[str]:
    """.notdef, space, then encoded glyphs by code point, then the rest by name."""
    encoded = sorted((min(g.unicodes), n) for n, g in glyphs.items() if g.unicodes)
    first = [n for n in (".notdef", "space") if n in glyphs]
    rest = [n for _, n in encoded if n not in first]
    unencoded = sorted(n for n, g in glyphs.items() if not g.unicodes and n not in first)
    return [*first, *rest, *unencoded]


def to_ufo(p: Params, glyphs: dict[str, Glyph]) -> ufoLib2.Font:
    font = ufoLib2.Font()
    info = font.info
    info.familyName = meta.FAMILY
    info.styleName = p.name
    info.versionMajor = meta.VERSION_MAJOR
    info.versionMinor = meta.VERSION_MINOR
    info.unitsPerEm = p.upm
    info.ascender = p.asc
    info.descender = p.desc
    info.xHeight = p.xh
    info.capHeight = p.cap
    info.italicAngle = -p.slant
    info.copyright = meta.COPYRIGHT
    info.openTypeNameLicense = meta.LICENSE
    info.openTypeNameLicenseURL = meta.LICENSE_URL
    info.openTypeNameDescription = meta.DESCRIPTION
    info.openTypeOS2VendorID = meta.VENDOR
    info.openTypeOS2Type = []  # installable embedding: no restrictions
    info.openTypeHeadCreated = _ufo_date(meta.EPOCH)
    # One line box on every platform: hhea, typo and win metrics agree, and USE_TYPO_METRICS says so.
    info.openTypeHheaAscender = round(p.line_top)
    info.openTypeHheaDescender = round(p.line_bot)
    info.openTypeHheaLineGap = 0
    info.openTypeOS2TypoAscender = round(p.line_top)
    info.openTypeOS2TypoDescender = round(p.line_bot)
    info.openTypeOS2TypoLineGap = 0
    info.openTypeOS2WinAscent = round(p.line_top)
    info.openTypeOS2WinDescent = round(-p.line_bot)
    info.openTypeOS2Selection = [7]
    info.openTypeOS2WeightClass = round(p.wght)
    info.openTypeOS2WidthClass = 5  # ty: ignore[invalid-assignment]  (ufoLib2 converts the number)
    info.openTypeOS2Panose = [2, 11, _panose_weight(p.wght), 9, 2, 2, 3, 2, 2, 4]
    info.openTypeOS2StrikeoutSize = round(p.op * 0.8)
    info.openTypeOS2StrikeoutPosition = round(p.xh * 0.5 + p.op * 0.4)
    info.postscriptIsFixedPitch = True
    info.postscriptUnderlineThickness = round(p.op * 0.8)
    info.postscriptUnderlinePosition = -130
    info.postscriptBlueValues = [
        round(v) for v in (-p.over, 0, p.xh, p.xh + p.over, p.cap, p.cap + p.over, p.asc, p.asc + p.over)
    ]
    info.postscriptOtherBlues = [round(p.desc - p.over), round(p.desc)]
    info.postscriptStemSnapH = sorted({round(p.hair), round(p.cap_hair)})
    info.postscriptStemSnapV = sorted({round(p.stem), round(p.cap_stem)})
    info.openTypeGaspRangeRecords = [{"rangeMaxPPEM": 65535, "rangeGaspBehavior": [0, 1, 2, 3]}]  # ty: ignore[invalid-assignment]

    order = glyph_order(glyphs)
    for name in order:
        g = glyphs[name]
        ug = font.newGlyph(name)
        ug.width = g.advance
        ug.unicodes = list(g.unicodes)
        pen = ug.getPen()
        for c in g.contours:
            pen.moveTo(_xy(c.segs[0].start))
            segs = c.segs[:-1] if isinstance(c.segs[-1], Line) else c.segs  # closePath draws a closing line
            for s in segs:
                if isinstance(s, Line):
                    pen.lineTo(_xy(s.p1))
                else:
                    pen.curveTo(_xy(s.c1), _xy(s.c2), _xy(s.p3))
            pen.closePath()
        for base, offset in g.components:
            pen.addComponent(base, (1, 0, 0, 1, offset.real, offset.imag))
        for anchor, z in sorted(g.anchors.items()):
            ug.appendAnchor({"name": anchor, "x": z.real, "y": z.imag})
    font.lib["public.glyphOrder"] = order
    font.lib["public.openTypeCategories"] = {n: ("mark" if glyphs[n].mark else "base") for n in order if n != ".notdef"}
    font.features.text = feature_file(set(order))
    return font


def _xy(z: complex) -> tuple[float, float]:
    return (round(z.real, 3), round(z.imag, 3))


def _ufo_date(epoch: int) -> str:
    import datetime

    return datetime.datetime.fromtimestamp(epoch, datetime.UTC).strftime("%Y/%m/%d %H:%M:%S")


def _panose_weight(wght: float) -> int:
    return {300: 3, 400: 5, 500: 6, 600: 7, 700: 8}.get(round(wght), 5)


def designspace(italic: bool, master_dir: Path, masters: tuple[Params, ...]) -> DesignSpaceDocument:
    doc = DesignSpaceDocument()
    axis = AxisDescriptor()
    axis.name = "Weight"
    axis.tag = "wght"
    axis.minimum, axis.default, axis.maximum = 300, 400, 700
    axis.axisOrdering = 0
    axis.axisLabels = [
        AxisLabelDescriptor(
            name=name,
            userValue=wght,
            elidable=name == "Regular",
            linkedUserValue=700 if name == "Regular" else None,
        )
        for name, wght in meta.WEIGHTS
    ]
    doc.addAxis(axis)
    for p in masters:
        src = SourceDescriptor()
        src.path = str(master_dir / f"{meta.FAMILY}-{p.name.replace(' ', '')}.ufo")
        src.name = p.name
        src.familyName = meta.FAMILY
        src.styleName = p.name
        src.location = {"Weight": p.wght}
        doc.addSource(src)
    for style in STYLES:
        if style.italic != italic:
            continue
        inst = InstanceDescriptor()
        inst.name = f"{meta.FAMILY} {style.name}"
        inst.familyName = meta.FAMILY
        inst.styleName = style.name
        inst.postScriptFontName = style.file_stem
        inst.styleMapFamilyName = style.map_family
        inst.styleMapStyleName = style.map_style
        inst.location = {"Weight": style.wght}
        inst.filename = f"instances/{style.file_stem}.ufo"
        doc.addInstance(inst)
    return doc


def write_sources(build_dir: Path) -> dict[bool, Path]:
    """Draw every master and write the UFOs and the two designspaces. Returns the designspace paths by italic."""
    glyph_modules.load()
    for draft in filter(None, os.environ.get("RACHIS_DRAFTS", "").split(os.pathsep)):
        glyph_modules.load_file(draft)  # a preview build: glyph modules that are not in the package yet
    master_dir = build_dir / "masters"
    master_dir.mkdir(parents=True, exist_ok=True)
    out: dict[bool, Path] = {}
    for italic, masters in ((False, UPRIGHT_MASTERS), (True, ITALIC_MASTERS)):
        for p in masters:
            glyphs = build_all(p)
            ufo = to_ufo(p, glyphs)
            ufo.save(master_dir / f"{meta.FAMILY}-{p.name.replace(' ', '')}.ufo", overwrite=True)
        doc = designspace(italic, master_dir, masters)
        path = build_dir / f"{meta.FAMILY}{'-Italic' if italic else ''}.designspace"
        doc.write(path)
        out[italic] = path
    return out


# ---------------------------------------------------------------------------------------------------------------
# compiling


def _fontmake(args: list[str], cwd: Path) -> None:
    env = dict(os.environ, SOURCE_DATE_EPOCH=str(meta.EPOCH))
    cmd = [sys.executable, "-m", "fontmake", *args, "--no-production-names", "--verbose", "WARNING"]
    done = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True, check=False)
    if done.returncode != 0:
        raise RuntimeError(f"fontmake failed:\n{done.stdout[-3000:]}\n{done.stderr[-6000:]}")


def variable_name(italic: bool) -> str:
    return f"{meta.FAMILY}{'-Italic' if italic else ''}[wght].ttf"


def compile_all(build_dir: Path, sources: dict[bool, Path], statics: bool = True) -> dict[str, list[Path]]:
    """Run fontmake. Returns the raw outputs by kind: 'variable', 'ttf', 'otf'."""
    out: dict[str, list[Path]] = {"variable": [], "ttf": [], "otf": []}
    for italic, ds in sources.items():
        vf = build_dir / "variable" / variable_name(italic)
        vf.parent.mkdir(parents=True, exist_ok=True)
        _fontmake(["-m", str(ds), "-o", "variable", "--output-path", str(vf)], build_dir)
        out["variable"].append(vf)
        if statics:
            for kind in ("ttf", "otf"):
                d = build_dir / kind
                _fontmake(
                    ["-m", str(ds), "-o", kind, "-i", "--output-dir", str(d), "--overlaps-backend", "pathops"],
                    build_dir,
                )
    if statics:
        for kind in ("ttf", "otf"):
            out[kind] = sorted((build_dir / kind).glob(f"*.{kind}"))
    return out


# ---------------------------------------------------------------------------------------------------------------
# finishing


def _style_of(path: Path) -> Style:
    for s in STYLES:
        if path.stem == s.file_stem:
            return s
    raise KeyError(path.name)


def _stat(font: TTFont, italic: bool, wght: int | None) -> None:
    """A STAT table that places the font in the family: its weight (a range, for a variable font) and whether it
    is the italic, with the upright linked to the italic."""
    weights = [
        {"value": w, "name": name, **({"flags": 0x2, "linkedValue": 700} if name == "Regular" else {})}
        for name, w in meta.WEIGHTS
    ]
    if wght is not None:
        weights = [v for v in weights if v["value"] == wght] or [{"value": wght, "name": str(wght)}]
    ital = {"value": 1, "name": "Italic"} if italic else {"value": 0, "name": "Roman", "flags": 0x2, "linkedValue": 1}
    axes = [
        {"tag": "wght", "name": "Weight", "ordering": 0, "values": weights},
        {"tag": "ital", "name": "Italic", "ordering": 1, "values": [ital]},
    ]
    buildStatTable(font, axes, elidedFallbackName=2)


def _set_overlap_flags(font: TTFont) -> None:
    """A variable font keeps its strokes as overlapping contours. The flags tell rasterisers to fill them as one
    shape."""
    glyf = font["glyf"]
    for name in font.getGlyphOrder():
        g = glyf[name]
        if g.isComposite():
            g.components[0].flags |= _g_l_y_f.OVERLAP_COMPOUND
        elif g.numberOfContours > 0:
            g.flags[0] |= _g_l_y_f.flagOverlapSimple


def _common(font: TTFont) -> None:
    advance = font["hmtx"]["space"][0] if "space" in font["hmtx"].metrics else 600
    font["OS/2"].xAvgCharWidth = advance  # the spec's value for a monospaced font; marks have no advance
    font["post"].isFixedPitch = 1  # ty: ignore[missing-attribute]


def finish_variable(src: Path, dst: Path, italic: bool) -> None:
    font = TTFont(src)
    _common(font)
    _set_overlap_flags(font)
    _stat(font, italic, None)
    dst.parent.mkdir(parents=True, exist_ok=True)
    _save(font, dst)


def finish_static(src: Path, dst: Path, hint: bool) -> None:
    style = _style_of(src)
    font = TTFont(src)
    _common(font)
    _stat(font, style.italic, style.wght)
    dst.parent.mkdir(parents=True, exist_ok=True)
    _save(font, dst)
    if hint and dst.suffix == ".ttf":
        _autohint(dst)


def _autohint(path: Path) -> None:
    """Hint a static TrueType font with ttfautohint, for rasterisers that still snap to the pixel grid."""
    from ttfautohint import ttfautohint
    from ttfautohint.options import StemWidthMode

    data = ttfautohint(
        in_buffer=path.read_bytes(),
        no_info=True,  # no version string in the name table: it would differ between ttfautohint versions
        hinting_range_min=7,
        hinting_range_max=48,
        hinting_limit=96,
        gray_stem_width_mode=StemWidthMode.NATURAL,
        gdi_cleartype_stem_width_mode=StemWidthMode.QUANTIZED,
        dw_cleartype_stem_width_mode=StemWidthMode.NATURAL,
        windows_compatibility=False,
        symbol=False,
        epoch=meta.EPOCH,
    )
    path.write_bytes(data)
    font = TTFont(path)
    font["head"].flags |= 1 << 3  # hinted: round the ppem to an integer  # ty: ignore[missing-attribute]
    _save(font, path)


def _save(font: TTFont, path: Path) -> None:
    os.environ["SOURCE_DATE_EPOCH"] = str(meta.EPOCH)
    font.save(path)


def to_woff2(src: Path, dst: Path) -> None:
    font = TTFont(src)
    font.flavor = "woff2"
    dst.parent.mkdir(parents=True, exist_ok=True)
    _save(font, dst)


def write_manifest(fonts_dir: Path) -> Path:
    """SHA-256 of every font file, in the format ``sha256sum -c`` reads."""
    lines = []
    for path in sorted(p for p in fonts_dir.rglob("*") if p.is_file() and p.suffix in (".ttf", ".otf", ".woff2")):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        lines.append(f"{digest}  {path.relative_to(fonts_dir).as_posix()}")
    out = fonts_dir / "SHA256SUMS"
    out.write_text("\n".join(lines) + "\n")
    return out


def build(
    fonts_dir: Path | None = None, build_dir: Path | None = None, statics: bool = True, hint: bool = True
) -> Path:
    """Build every font into ``fonts_dir`` (default: the project's ``fonts/``)."""
    fonts_dir = fonts_dir or ROOT / "fonts"
    build_dir = build_dir or ROOT / "build"
    shutil.rmtree(build_dir, ignore_errors=True)
    build_dir.mkdir(parents=True)
    REGISTRY.clear()
    for module in [m for m in sys.modules if m.startswith("rachis.glyphs.")]:
        del sys.modules[module]
    sources = write_sources(build_dir)
    raw = compile_all(build_dir, sources, statics)

    for sub in ("variable", "ttf", "otf", "webfonts"):
        shutil.rmtree(fonts_dir / sub, ignore_errors=True)
    for italic, src in zip(sources, raw["variable"], strict=True):
        dst = fonts_dir / "variable" / src.name
        finish_variable(src, dst, italic)
        to_woff2(dst, fonts_dir / "webfonts" / dst.with_suffix(".woff2").name)
    for kind in ("ttf", "otf"):
        for src in raw[kind]:
            dst = fonts_dir / kind / src.name
            finish_static(src, dst, hint)
            if kind == "ttf":
                to_woff2(dst, fonts_dir / "webfonts" / dst.with_suffix(".woff2").name)
    write_manifest(fonts_dir)
    return fonts_dir


__all__ = ["SLANT", "STYLES", "Style", "build", "write_sources"]
