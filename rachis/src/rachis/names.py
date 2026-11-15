"""Glyph names. Every encoded glyph has one canonical name, derived from its code point, so that a module can
refer to a glyph another module draws without the two agreeing on a spelling."""

from __future__ import annotations

from fontTools import agl

# Names for a few characters the Adobe Glyph List leaves to the uniXXXX form but which are referred to often.
_FRIENDLY = {0x00A0: "nbspace", 0x00AD: "softhyphen", 0x0131: "dotlessi", 0x0237: "dotlessj"}


def name_of(char: str | int) -> str:
    """The canonical glyph name of a character.

    Basic Latin, Latin-1 and Latin Extended-A use their Adobe Glyph List names (``a``, ``zero``, ``period``,
    ``hyphen``, ``eacute``, ``Amacron``); everything else is ``uniXXXX`` (``uXXXXX`` above the Basic Multilingual
    Plane).
    """
    cp = char if isinstance(char, int) else ord(char)
    if cp in _FRIENDLY:
        return _FRIENDLY[cp]
    if cp < 0x0180 and cp in agl.UV2AGL:
        found = agl.UV2AGL[cp]
        return found if isinstance(found, str) else found[0]
    return f"uni{cp:04X}" if cp <= 0xFFFF else f"u{cp:05X}"
