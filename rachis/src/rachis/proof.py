"""Proofs: pictures of glyphs for the eye to judge, drawn without the full build.

``quick_font`` compiles glyphs into an in-memory OpenType font in well under a second, with overlaps left in.
``text_sheet`` sets lines of text with it at several sizes through FreeType; ``outline_sheet`` draws each glyph
large with its contours, points, handles and the font's horizontal lines.
"""

from __future__ import annotations

import contextlib
import io
from collections.abc import Sequence

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.t2CharStringPen import T2CharStringPen
from PIL import Image, ImageDraw, ImageFont

from rachis.geom import Cubic, Line, flatten
from rachis.glyph import Glyph
from rachis.params import Params
from rachis.pen import Contour


def _draw_contour(pen: T2CharStringPen, c: Contour, offset: complex = 0j) -> None:
    def xy(z: complex) -> tuple[float, float]:
        z += offset
        return (round(z.real), round(z.imag))

    pen.moveTo(xy(c.segs[0].start))
    for s in c.segs:
        if isinstance(s, Line):
            pen.lineTo(xy(s.p1))
        else:
            pen.curveTo(xy(s.c1), xy(s.c2), xy(s.p3))
    pen.closePath()


def flat_contours(glyphs: dict[str, Glyph], name: str, offset: complex = 0j) -> list[tuple[Contour, complex]]:
    """The contours of ``name`` with its components resolved, each with the offset to draw it at."""
    g = glyphs[name]
    out = [(c, offset) for c in g.contours]
    for base, d in g.components:
        out.extend(flat_contours(glyphs, base, offset + d))
    return out


def quick_font(glyphs: dict[str, Glyph], p: Params, family: str = "RachisProof") -> bytes:
    names = [".notdef", *sorted(n for n in glyphs if n != ".notdef")]
    fb = FontBuilder(p.upm, isTTF=False)
    fb.setupGlyphOrder(names)
    cmap = {cp: g.name for g in glyphs.values() for cp in g.unicodes}
    fb.setupCharacterMap(cmap)
    charstrings = {}
    metrics = {}
    for n in names:
        g = glyphs.get(n)
        pen = T2CharStringPen(p.width if g is None else g.advance, None)
        if g is not None:
            for c, off in flat_contours(glyphs, n):
                _draw_contour(pen, c, off)
        charstrings[n] = pen.getCharString()
        metrics[n] = (round(p.width if g is None else g.advance), 0)
    fb.setupCFF(family, {"FullName": family}, charstrings, {})
    fb.setupHorizontalMetrics(metrics)
    fb.setupHorizontalHeader(ascent=round(p.asc + 200), descent=round(p.desc - 60))
    fb.setupNameTable({"familyName": family, "styleName": p.name})
    fb.setupOS2(sTypoAscender=round(p.asc + 200), sTypoDescender=round(p.desc - 60), usWinAscent=1000, usWinDescent=300)
    fb.setupPost()
    buf = io.BytesIO()
    fb.save(buf)
    return buf.getvalue()


def text_sheet(
    font_bytes: bytes,
    lines: Sequence[str],
    sizes: Sequence[int] = (96, 48, 24, 16, 13),
    dark: bool = False,
    scale: int = 1,
    line_height: float = 1.3,
    width: int | None = None,
) -> Image.Image:
    """``lines`` set at each of ``sizes`` (pixels per em), stacked. ``scale`` enlarges small sizes by pixel
    replication so that their rasterisation can be inspected."""
    bg, fg = ((18, 18, 20), (232, 232, 228)) if dark else ((255, 255, 255), (16, 16, 16))
    blocks: list[Image.Image] = []
    for size in sizes:
        font = ImageFont.truetype(io.BytesIO(font_bytes), size)
        lh = round(size * line_height)
        w = max(round(font.getlength(line)) for line in lines) + size
        im = Image.new("RGB", (w, lh * len(lines) + size // 2), bg)
        d = ImageDraw.Draw(im)
        for i, line in enumerate(lines):
            d.text((size // 2, size // 4 + i * lh), line, font=font, fill=fg)
        if scale > 1 and size <= 24:
            im = im.resize((im.width * scale, im.height * scale), Image.Resampling.NEAREST)
        blocks.append(im)
    total_w = max(b.width for b in blocks) if width is None else width
    sheet = Image.new("RGB", (total_w, sum(b.height for b in blocks)), bg)
    y = 0
    for b in blocks:
        sheet.paste(b, (0, y))
        y += b.height
    return sheet


def outline_sheet(
    glyphs: dict[str, Glyph],
    p: Params,
    names: Sequence[str],
    em_px: int = 520,
    columns: int = 4,
    points: bool = True,
) -> Image.Image:
    """Each glyph drawn large: its filled shape in grey, contours in black, on-curve points as squares, handles as
    circles, with the baseline, x-height, cap height, ascender, descender and the cell's edges."""
    s = em_px / p.upm
    top, bottom = p.asc + 110, p.desc - 90
    cell_w = round((p.width + 160) * s)
    cell_h = round((top - bottom) * s)
    rows = (len(names) + columns - 1) // columns
    im = Image.new("RGB", (cell_w * columns, cell_h * rows), (255, 255, 255))
    d = ImageDraw.Draw(im, "RGBA")
    label_font = ImageFont.load_default(size=14)

    for i, name in enumerate(names):
        ox = (i % columns) * cell_w + round(80 * s)
        oy = (i // columns) * cell_h

        def px(z: complex, ox: int = ox, oy: int = oy) -> tuple[float, float]:
            return (ox + z.real * s, oy + (top - z.imag) * s)

        g = glyphs[name]
        for y, colour in (
            (0, (200, 60, 60)),
            (p.xh, (60, 120, 200)),
            (p.cap, (60, 160, 90)),
            (p.asc, (150, 150, 150)),
            (p.desc, (150, 150, 150)),
        ):
            d.line([px(complex(-70, y)), px(complex(g.advance + 70, y))], fill=(*colour, 150), width=1)
        for x in (0, g.advance):
            d.line([px(complex(x, bottom + 30)), px(complex(x, top - 30))], fill=(150, 150, 150, 160), width=1)
        d.text((ox - round(70 * s), oy + 4), name, fill=(90, 90, 90), font=label_font)

        flat = flat_contours(glyphs, name)
        for c, off in flat:
            poly = [px(c.segs[0].start + off)]
            for seg in c.segs:
                poly.extend(px(q + off) for q in flatten(seg, 0.2))
            d.polygon(poly, fill=(0, 0, 0, 46))
            d.line([*poly, poly[0]], fill=(0, 0, 0, 255), width=2)
        if not points:
            continue
        for c, off in flat:
            for seg in c.segs:
                if isinstance(seg, Cubic):
                    for a, b in ((seg.p0, seg.c1), (seg.p3, seg.c2)):
                        d.line([px(a + off), px(b + off)], fill=(210, 90, 30, 200), width=1)
                        x, y = px(b + off)
                        d.ellipse([x - 3, y - 3, x + 3, y + 3], outline=(210, 90, 30, 255))
                x, y = px(seg.end + off)
                d.rectangle([x - 3, y - 3, x + 3, y + 3], fill=(20, 80, 200, 255))
    return im


def compare_sheet(
    rows: Sequence[tuple[str, ImageFont.FreeTypeFont]],
    lines: Sequence[str],
    size: int,
    dark: bool = False,
    scale: int = 1,
) -> Image.Image:
    """The same ``lines`` set in each of ``rows`` (a label and a loaded font), stacked and labelled."""
    bg, fg, dim = (
        ((18, 18, 20), (232, 232, 228), (120, 120, 120)) if dark else ((255, 255, 255), (16, 16, 16), (130, 130, 130))
    )
    label_font = ImageFont.load_default(size=13)
    lh = round(size * 1.32)
    gutter = 150
    width = gutter + max(round(font.getlength(line)) for _, font in rows for line in lines) + size
    block = lh * len(lines) + size // 3
    im = Image.new("RGB", (width, block * len(rows)), bg)
    d = ImageDraw.Draw(im)
    for i, (label, font) in enumerate(rows):
        d.text((6, i * block + size // 3), label, font=label_font, fill=dim)
        for j, line in enumerate(lines):
            d.text((gutter, i * block + size // 6 + j * lh), line, font=font, fill=fg)
    if scale > 1:
        im = im.resize((im.width * scale, im.height * scale), Image.Resampling.NEAREST)
    return im


def reference_fonts(directory: str, size: int) -> list[tuple[str, ImageFont.FreeTypeFont]]:
    """Fonts in ``directory`` (reference typefaces kept outside the repository), at their regular weight."""
    import os

    out: list[tuple[str, ImageFont.FreeTypeFont]] = []
    wanted = ("JetBrainsMono", "IBMPlexMono-Regular", "SourceCodePro", "FiraCode")
    for stem in wanted:
        for name in sorted(os.listdir(directory)) if os.path.isdir(directory) else []:
            if name.startswith(stem) and name.endswith((".ttf", ".otf")) and "Italic" not in name:
                font = ImageFont.truetype(os.path.join(directory, name), size)
                with contextlib.suppress(OSError):  # not a variable font
                    font.set_variation_by_axes([400])
                out.append((stem.split("-")[0], font))
                break
    return out
