"""The built fonts in ``fonts/``: what a terminal, an editor and a reader rely on.

These tests read the files that ship. ``test_build.py`` checks that the source still builds to exactly those files.
"""

from __future__ import annotations

import hashlib
import subprocess
import unicodedata
import unittest
from pathlib import Path

from fontTools.pens.boundsPen import BoundsPen
from fontTools.ttLib import TTFont

from rachis import meta

ROOT = Path(__file__).resolve().parents[1]
FONTS = ROOT / "fonts"
REPOSITORY = ROOT.parent

ADVANCE = 600
LINE_TOP, LINE_BOTTOM = 980, -270

# Characters whose glyphs are meant to touch or cross the sides of the cell.
BOX_DRAWING = range(0x2500, 0x25A0)
POWERLINE = range(0xE0A0, 0xE0C0)


def font_files() -> list[Path]:
    return sorted(p for p in FONTS.rglob("*") if p.suffix in (".ttf", ".otf"))


def joins_its_neighbours(cp: int) -> bool:
    """Whether a character's glyph is drawn to reach its neighbours' cells: lines, blocks, long dashes and arrows."""
    name = unicodedata.name(chr(cp), "")
    return (
        cp in BOX_DRAWING
        or cp in POWERLINE
        or cp in (0x2014, 0x2015)  # em dash, horizontal bar
        or "LONG " in name  # long arrows
        or "EXTENSION" in name
    )


def bounds(font: TTFont, glyph_name: str) -> tuple[float, float, float, float] | None:
    glyph_set = font.getGlyphSet()
    pen = BoundsPen(glyph_set)
    glyph_set[glyph_name].draw(pen)
    return pen.bounds


@unittest.skipUnless(FONTS.is_dir(), "no fonts/ directory: run `rachis build`")
class Shipped(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fonts = {p: TTFont(p) for p in font_files()}
        cls.regular = cls.fonts[FONTS / "ttf" / f"{meta.FAMILY}-Regular.ttf"]

    def test_the_family_is_complete(self) -> None:
        names = {p.relative_to(FONTS).as_posix() for p in self.fonts}
        styles = ["Light", "Regular", "Medium", "SemiBold", "Bold"]
        expected = {f"variable/{meta.FAMILY}[wght].ttf", f"variable/{meta.FAMILY}-Italic[wght].ttf"}
        for kind in ("ttf", "otf"):
            for s in styles:
                expected.add(f"{kind}/{meta.FAMILY}-{s}.{kind}")
                expected.add(f"{kind}/{meta.FAMILY}-{'Italic' if s == 'Regular' else s + 'Italic'}.{kind}")
        self.assertEqual(names, expected)

    def test_the_manifest_matches_the_files(self) -> None:
        listed = {}
        for line in (FONTS / "SHA256SUMS").read_text().splitlines():
            digest, name = line.split("  ", 1)
            listed[name] = digest
        actual = {
            p.relative_to(FONTS).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in FONTS.rglob("*")
            if p.suffix in (".ttf", ".otf", ".woff2")
        }
        self.assertEqual(listed, actual)

    def test_every_glyph_has_the_one_advance(self) -> None:
        for path, font in self.fonts.items():
            marks = set()
            if "GDEF" in font and font["GDEF"].table.GlyphClassDef:
                marks = {g for g, c in font["GDEF"].table.GlyphClassDef.classDefs.items() if c == 3}
            for name, (advance, _) in font["hmtx"].metrics.items():
                self.assertEqual(advance, 0 if name in marks else ADVANCE, f"{path.name}: {name}")

    def test_fonts_declare_themselves_monospaced(self) -> None:
        for path, font in self.fonts.items():
            self.assertEqual(font["post"].isFixedPitch, 1, path.name)
            self.assertEqual(font["OS/2"].panose.bProportion, 9, path.name)
            self.assertEqual(font["OS/2"].xAvgCharWidth, ADVANCE, path.name)
            self.assertEqual(font["hhea"].advanceWidthMax, ADVANCE, path.name)

    def test_one_line_box_in_every_table_of_every_font(self) -> None:
        for path, font in self.fonts.items():
            os2, hhea = font["OS/2"], font["hhea"]
            self.assertEqual((hhea.ascent, hhea.descent, hhea.lineGap), (LINE_TOP, LINE_BOTTOM, 0), path.name)
            self.assertEqual(
                (os2.sTypoAscender, os2.sTypoDescender, os2.sTypoLineGap), (LINE_TOP, LINE_BOTTOM, 0), path.name
            )
            self.assertEqual((os2.usWinAscent, os2.usWinDescent), (LINE_TOP, -LINE_BOTTOM), path.name)
            self.assertTrue(os2.fsSelection & (1 << 7), f"{path.name}: USE_TYPO_METRICS")

    def test_nothing_is_drawn_outside_the_line(self) -> None:
        # A terminal clips a glyph at its cell, so anything above or below the line box would be cut off.
        for path, font in self.fonts.items():
            if "Italic" in path.name:
                continue
            for name in font.getGlyphOrder():
                box = bounds(font, name)
                if box is None:
                    continue
                self.assertGreaterEqual(box[1], LINE_BOTTOM - 1, f"{path.name}: {name}")
                self.assertLessEqual(box[3], LINE_TOP + 1, f"{path.name}: {name}")

    def test_upright_glyphs_stay_inside_their_cell(self) -> None:
        font = self.regular
        marks = (
            {g for g, c in font["GDEF"].table.GlyphClassDef.classDefs.items() if c == 3} if "GDEF" in font else set()
        )
        for cp, name in font.getBestCmap().items():
            if joins_its_neighbours(cp) or name in marks:
                continue
            box = bounds(font, name)
            if box is None:
                continue
            self.assertGreaterEqual(box[0], -1, f"U+{cp:04X} {name}")
            self.assertLessEqual(box[2], ADVANCE + 1, f"U+{cp:04X} {name}")

    def test_no_substitution_replaces_or_depends_on_neighbours(self) -> None:
        # Decision T06: no ligatures and nothing contextual. Every GSUB lookup is a single substitution.
        allowed = {"ss01", "ss02", "sups", "subs", "sinf", "aalt", "ccmp", "locl"}
        for path, font in self.fonts.items():
            if "GSUB" not in font:
                continue
            table = font["GSUB"].table
            tags = {record.FeatureTag for record in table.FeatureList.FeatureRecord}
            self.assertLessEqual(tags, allowed, path.name)
            for lookup in table.LookupList.Lookup:
                self.assertEqual(
                    lookup.LookupType, 1, f"{path.name}: lookup type {lookup.LookupType} is not a single substitution"
                )

    def test_box_drawing_reaches_the_edges_of_the_cell(self) -> None:
        font = self.regular
        cmap = font.getBestCmap()
        horizontal = bounds(font, cmap[0x2500])
        vertical = bounds(font, cmap[0x2502])
        cross = bounds(font, cmap[0x253C])
        full = bounds(font, cmap[0x2588])
        assert horizontal and vertical and cross and full
        self.assertEqual((horizontal[0], horizontal[2]), (0, ADVANCE))
        self.assertEqual((vertical[1], vertical[3]), (LINE_BOTTOM, LINE_TOP))
        self.assertEqual(cross, (0, LINE_BOTTOM, ADVANCE, LINE_TOP))
        self.assertEqual(full, (0, LINE_BOTTOM, ADVANCE, LINE_TOP))
        # the horizontal line and the vertical line cross at the centre of the cell
        self.assertAlmostEqual((horizontal[1] + horizontal[3]) / 2, (LINE_TOP + LINE_BOTTOM) / 2, delta=1)
        self.assertAlmostEqual((vertical[0] + vertical[2]) / 2, ADVANCE / 2, delta=1)

    def test_the_whole_box_drawing_block_elements_and_braille_are_present(self) -> None:
        cmap = self.regular.getBestCmap()
        for block in (range(0x2500, 0x2580), range(0x2580, 0x25A0), range(0x2800, 0x2900)):
            missing = [f"U+{cp:04X}" for cp in block if cp not in cmap]
            self.assertEqual(missing, [])

    def test_ascii_and_latin_1_are_present(self) -> None:
        cmap = self.regular.getBestCmap()
        wanted = [*range(0x20, 0x7F), *range(0xA0, 0x100)]
        self.assertEqual([f"U+{cp:04X}" for cp in wanted if cp not in cmap], [])

    def test_every_font_has_the_same_characters(self) -> None:
        reference = set(self.regular.getBestCmap())
        for path, font in self.fonts.items():
            self.assertEqual(set(font.getBestCmap()), reference, path.name)

    def test_the_repository_is_covered(self) -> None:
        """Every character in the repository's tracked text files has a glyph, apart from emoji, CJK and controls."""
        cmap = self.regular.getBestCmap()
        listed = subprocess.run(["git", "ls-files"], cwd=REPOSITORY, capture_output=True, text=True, check=True).stdout
        missing: dict[str, str] = {}
        for rel in listed.splitlines():
            path = REPOSITORY / rel
            if not path.is_file() or path.suffix in (".ttf", ".otf", ".woff2", ".png", ".lock"):
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            for ch in set(text):
                cp = ord(ch)
                if cp in cmap or cp < 0x20 or unicodedata.category(ch) in ("Cc", "Cf", "Zl", "Zp"):
                    continue
                if cp >= 0x1F000 or 0x2E80 <= cp <= 0x9FFF or 0xFE00 <= cp <= 0xFE0F:  # emoji, CJK, variation selectors
                    continue
                missing.setdefault(f"U+{cp:04X} {unicodedata.name(ch, '?')}", rel)
        self.assertEqual(missing, {})

    def test_variable_fonts_have_the_weight_axis_and_flag_their_overlaps(self) -> None:
        for path, font in self.fonts.items():
            if "fvar" not in font:
                continue
            (axis,) = font["fvar"].axes
            self.assertEqual((axis.axisTag, axis.minValue, axis.defaultValue, axis.maxValue), ("wght", 300, 400, 700))
            names = [font["name"].getDebugName(i.subfamilyNameID) for i in font["fvar"].instances]
            italic = "Italic" in path.name
            want = ["Light", "Regular", "Medium", "SemiBold", "Bold"]
            if italic:
                want = ["Light Italic", "Italic", "Medium Italic", "SemiBold Italic", "Bold Italic"]
            self.assertEqual(names, want, path.name)
            glyf = font["glyf"]
            for name in font.getGlyphOrder():
                g = glyf[name]
                if g.numberOfContours > 1:
                    self.assertTrue(g.flags[0] & 0x40, f"{path.name}: {name} lacks the overlap flag")

    def test_names_link_the_four_styles_and_group_the_rest(self) -> None:
        for path, font in self.fonts.items():
            if "fvar" in font:
                continue
            name = font["name"]
            style = path.stem.split("-", 1)[1]
            family, sub = name.getDebugName(1), name.getDebugName(2)
            italic = "Italic" in style
            weight = style.replace("Italic", "") or "Regular"
            if weight in ("Regular", "Bold"):
                self.assertEqual(family, meta.FAMILY, path.name)
                self.assertEqual(
                    sub,
                    {"Regular": "Regular", "Bold": "Bold"}[weight] + (" Italic" if italic else "")
                    if weight == "Bold" or not italic
                    else "Italic",
                    path.name,
                )
                self.assertIsNone(name.getDebugName(16), path.name)
            else:
                self.assertEqual(family, f"{meta.FAMILY} {weight}", path.name)
                self.assertEqual(sub, "Italic" if italic else "Regular", path.name)
                self.assertEqual(name.getDebugName(16), meta.FAMILY, path.name)
            self.assertEqual(bool(font["OS/2"].fsSelection & 1), italic, path.name)
            self.assertEqual(bool(font["head"].macStyle & 2), italic, path.name)
            self.assertEqual(bool(font["OS/2"].fsSelection & (1 << 5)), weight == "Bold", path.name)

    def test_stylistic_sets_swap_the_zero(self) -> None:
        import uharfbuzz as hb

        path = FONTS / "ttf" / f"{meta.FAMILY}-Regular.ttf"
        face = hb.Face(path.read_bytes())
        font = hb.Font(face)

        def shape(text: str, features: dict[str, bool]) -> list[str]:
            buf = hb.Buffer()
            buf.add_str(text)
            buf.guess_segment_properties()
            hb.shape(font, buf, features)
            return [font.glyph_to_string(info.codepoint) for info in buf.glyph_infos]

        self.assertEqual(shape("0", {}), ["zero"])
        self.assertEqual(shape("0", {"ss01": True}), ["zero.dot"])
        self.assertEqual(shape("0", {"ss02": True}), ["zero.plain"])
        self.assertEqual(shape("->", {}), ["hyphen", "greater"])
        self.assertEqual(shape("!=", {"liga": True, "calt": True, "dlig": True}), ["exclam", "equal"])
        self.assertEqual(
            shape("x2", {"sups": True}), ["x", "uni00B2"] if "uni00B2" in face.glyph_names else ["x", "twosuperior"]
        )


if __name__ == "__main__":
    unittest.main()
