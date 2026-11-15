"""OpenType layout features, written for the glyphs a build actually has.

The typeface has no ligatures and nothing contextual: a feature here only ever replaces one glyph by one
alternate of the same character, at the reader's request. Mark positioning is added by the compiler from the
anchors the glyphs carry.
"""

from __future__ import annotations

from rachis.names import name_of

# Stylistic sets: tag -> (name shown by applications, substitutions as (character, alternate glyph name)).
STYLISTIC_SETS: dict[str, tuple[str, tuple[tuple[str, str], ...]]] = {
    "ss01": ("Dotted zero", (("0", "zero.dot"),)),
    "ss02": ("Plain zero", (("0", "zero.plain"),)),
}

SUPERIORS = dict(zip("0123456789+-=()ni", "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾ⁿⁱ", strict=True))
INFERIORS = dict(zip("0123456789+-=()", "₀₁₂₃₄₅₆₇₈₉₊₋₌₍₎", strict=True))


def feature_file(glyphs: set[str]) -> str:
    """The feature file for a font that has ``glyphs``. Rules that name a missing glyph are left out."""
    out: list[str] = [
        "languagesystem DFLT dflt;",
        "languagesystem latn dflt;",
        "languagesystem grek dflt;",
        "",
    ]

    def single(tag: str, pairs: list[tuple[str, str]], names: str | None = None) -> None:
        pairs = [(a, b) for a, b in pairs if a in glyphs and b in glyphs]
        if not pairs:
            return
        out.append(f"feature {tag} {{")
        if names:
            out.append(f'    featureNames {{ name "{names}"; }};')
        out.extend(f"    sub {a} by {b};" for a, b in pairs)
        out.append(f"}} {tag};")
        out.append("")

    for tag, (label, subs) in STYLISTIC_SETS.items():
        single(tag, [(name_of(ch), alt) for ch, alt in subs], label)
    single("sups", [(name_of(a), name_of(b)) for a, b in SUPERIORS.items()])
    single("subs", [(name_of(a), name_of(b)) for a, b in INFERIORS.items()])
    single("sinf", [(name_of(a), name_of(b)) for a, b in INFERIORS.items()])
    return "\n".join(out)
