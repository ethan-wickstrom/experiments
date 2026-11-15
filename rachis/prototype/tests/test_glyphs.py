"""The glyph programs: every one builds for every master, and the masters of a variable font agree in structure."""

from __future__ import annotations

import unicodedata
import unittest

from rachis import glyphs as glyph_modules
from rachis.check import check_glyphs
from rachis.glyph import REGISTRY
from rachis.names import name_of


class Programs(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        glyph_modules.load()

    def test_every_glyph_builds_and_masters_are_compatible(self) -> None:
        problems, _ = check_glyphs()
        self.assertEqual(problems, [])

    def test_no_character_is_drawn_twice(self) -> None:
        seen: dict[int, str] = {}
        for spec in REGISTRY.values():
            for cp in spec.unicodes:
                self.assertNotIn(cp, seen, f"U+{cp:04X} is encoded by {seen.get(cp)} and {spec.name}")
                seen[cp] = spec.name

    def test_names_are_canonical(self) -> None:
        # A glyph that encodes one character is named for it, so that any module can refer to it by character.
        for spec in REGISTRY.values():
            if len(spec.unicodes) == 1:
                self.assertEqual(spec.name, name_of(spec.unicodes[0]), f"U+{spec.unicodes[0]:04X}")

    def test_unencoded_glyphs_are_alternates_or_special(self) -> None:
        for spec in REGISTRY.values():
            if not spec.unicodes:
                self.assertTrue(spec.name == ".notdef" or "." in spec.name, spec.name)

    def test_combining_marks_have_no_advance(self) -> None:
        for spec in REGISTRY.values():
            for cp in spec.unicodes:
                if unicodedata.category(chr(cp)) in ("Mn", "Me"):
                    self.assertTrue(spec.mark, f"{spec.name} is a combining mark and must be registered with mark=True")


if __name__ == "__main__":
    unittest.main()
