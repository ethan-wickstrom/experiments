"""The measurements document: the fonts' numbers beside reference typefaces', as Markdown tables."""

from __future__ import annotations

import statistics
from pathlib import Path

from rachis import meta
from rachis.measure import ALPHANUMERIC, WATCHED, Renderer, Viewing, load_font, proportions

# Reference typefaces, by the file name each starts with in the reference directory.
REFERENCES = (
    ("JetBrains Mono", "JetBrainsMono"),
    ("IBM Plex Mono", "IBMPlexMono-Regular"),
    ("Source Code Pro", "SourceCodePro"),
    ("Fira Code", "FiraCode"),
    ("DejaVu Sans Mono", "DejaVuSansMono"),
)

# The pairs the build gates on, with the least distance each must reach (docs/decisions.md, T07).
GATES: dict[tuple[str, str], float] = {
    ("0", "O"): 0.30,
    ("0", "8"): 0.25,
    ("O", "D"): 0.25,
    ("8", "B"): 0.25,
    ("5", "S"): 0.25,
    ("1", "l"): 0.40,
    ("1", "I"): 0.40,
    ("l", "I"): 0.40,
    ("l", "|"): 0.40,
    ("I", "|"): 0.40,
    ("g", "q"): 0.35,
}
GATE_VIEW = Viewing(px=14.0, sigma=1.0)


def find_references(directory: Path | None) -> list[tuple[str, Path]]:
    out: list[tuple[str, Path]] = []
    places = [directory] if directory else []
    places.append(Path("/usr/share/fonts/truetype/dejavu"))
    for label, stem in REFERENCES:
        for place in places:
            if place is None or not place.is_dir():
                continue
            hits = sorted(
                p
                for p in place.iterdir()
                if p.name.startswith(stem)
                and "Italic" not in p.name
                and "Oblique" not in p.name
                and "Bold" not in p.name
            )
            if hits:
                out.append((label, hits[0]))
                break
    return out


def measurements_markdown(fonts_dir: Path, refs_dir: Path | None) -> str:
    ours = fonts_dir / "ttf" / f"{meta.FAMILY}-Regular.ttf"
    fonts = [(meta.FAMILY, ours), *find_references(refs_dir)]
    lines: list[str] = []

    lines.append("## Proportions")
    lines.append("")
    lines.append("Regular weight, in thousandths of the em, read from the outlines.")
    lines.append("")
    head = [
        "",
        "advance",
        "x-height",
        "cap",
        "ascender",
        "descender",
        "stem",
        "hair",
        "stem / x-height",
        "stem / hair",
        "advance / x-height",
        "n counter / x-height",
        "gap / counter",
        "zero / O width",
    ]
    lines.append("| " + " | ".join(head) + " |")
    lines.append("|" + "---|" * len(head))
    for label, path in fonts:
        p = proportions(load_font(path))
        cells = [
            label,
            f"{p.advance:.0f}",
            f"{p.x_height:.0f}",
            f"{p.cap_height:.0f}",
            f"{p.ascender:.0f}",
            f"{p.descender:.0f}",
            f"{p.stem:.0f}",
            f"{p.hair:.0f}",
            f"{p.stem_to_x_height:.3f}",
            f"{p.stem_to_hair:.2f}",
            f"{p.advance_to_x_height:.2f}",
            f"{p.counter_to_x_height:.2f}",
            f"{p.gap_to_counter:.2f}",
            f"{p.zero_to_o:.2f}",
        ]
        lines.append("| " + " | ".join(cells) + " |")
    lines.append("")

    for view, title in (
        (Viewing(14.0, 1.0), "14 px, blur 1.0 px (the gate)"),
        (Viewing(14.0, 0.6), "14 px, blur 0.6 px"),
        (Viewing(13.0, 1.5), "13 px, blur 1.5 px"),
    ):
        renderers = [(label, Renderer(path, view)) for label, path in fonts]
        lines.append(f"## Distances at {title}")
        lines.append("")
        lines.append("| pair | gate | " + " | ".join(label for label, _ in fonts) + " |")
        lines.append("|---|---|" + "---|" * len(fonts))
        for a, b in WATCHED:
            gate = GATES.get((a, b))
            shown = f"`{a}` `{b}`".replace("|", "\\|")
            row = [shown, f"{gate:.2f}" if gate is not None and view == GATE_VIEW else ""]
            row.extend(f"{r.distance(a, b):.2f}" for _, r in renderers)
            lines.append("| " + " | ".join(row) + " |")
        lines.append("")
        lines.append("All 1891 pairs of the 62 letters and figures:")
        lines.append("")
        lines.append("| | closest pair | pairs under 0.20 | median |")
        lines.append("|---|---|---|---|")
        for label, r in renderers:
            every = sorted((r.distance(a, b), a, b) for i, a in enumerate(ALPHANUMERIC) for b in ALPHANUMERIC[i + 1 :])
            d, a, b = every[0]
            under = sum(1 for e in every if e[0] < 0.20)
            median = statistics.median(e[0] for e in every)
            lines.append(f"| {label} | `{a}` `{b}` {d:.2f} | {under} | {median:.2f} |")
        lines.append("")
    return "\n".join(lines)
