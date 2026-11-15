"""Command line: ``rachis proof`` draws pictures of glyphs, ``rachis build`` makes the fonts."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from rachis import glyphs as glyph_modules
from rachis.glyph import REGISTRY, build_all
from rachis.params import MASTERS, Params

if TYPE_CHECKING:
    from PIL import Image


def _master(name: str) -> Params:
    try:
        return MASTERS[name]
    except KeyError:
        raise SystemExit(f"no master named {name!r}; there are: {', '.join(MASTERS)}") from None


def _names_for(text: str) -> list[str]:
    by_cp = {cp: s.name for s in REGISTRY.values() for cp in s.unicodes}
    missing = sorted({ch for ch in text if ord(ch) not in by_cp and ch != "\n"})
    if missing:
        print(f"note: no glyph for {' '.join(f'U+{ord(c):04X}' for c in missing)}", file=sys.stderr)
    return [by_cp[ord(ch)] for ch in text if ord(ch) in by_cp]


def _load(args: argparse.Namespace) -> None:
    if not args.only_drafts:
        glyph_modules.load()
    for path in args.draft or []:
        glyph_modules.load_file(path)


def cmd_proof(args: argparse.Namespace) -> int:
    import io
    import os

    from PIL import ImageFont

    from rachis import proof

    _load(args)
    masters = list(MASTERS.values()) if args.masters else [_master(args.master)]
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    if args.outline is not None:
        literal = [n for n in args.outline if n in REGISTRY]
        names = list(dict.fromkeys([*literal, *_names_for("".join(n for n in args.outline if n not in REGISTRY))]))
        sheets = []
        for p in masters:
            built = build_all(p, names)
            sheets.append(
                proof.outline_sheet(built, p, names, em_px=args.em, columns=args.columns, points=not args.no_points)
            )
        image = _stack(sheets)
    else:
        lines = args.text or []
        wanted = None if args.all else list(dict.fromkeys([*_names_for("".join(lines)), "space"]))
        rows: list[tuple[str, ImageFont.FreeTypeFont]] = []
        fonts = []
        for p in masters:
            built = build_all(p, [n for n in wanted if n in REGISTRY] if wanted is not None else None)
            fonts.append((p, proof.quick_font(built, p)))
        if args.compare or args.masters:
            sheets = []
            for size in args.sizes:
                rows = [(p.name, ImageFont.truetype(io.BytesIO(data), size)) for p, data in fonts]
                if args.compare:
                    rows.extend(proof.reference_fonts(os.environ.get("RACHIS_REFS", ""), size))
                sheets.append(
                    proof.compare_sheet(rows, lines, size, dark=args.dark, scale=args.scale if size <= 24 else 1)
                )
            image = _stack(sheets)
        else:
            image = proof.text_sheet(fonts[0][1], lines, sizes=args.sizes, dark=args.dark, scale=args.scale)
    image.save(out)
    print(out, f"{image.width}x{image.height}")
    return 0


def _stack(images: list[Image.Image]) -> Image.Image:
    from PIL import Image

    if len(images) == 1:
        return images[0]
    sheet = Image.new("RGB", (max(i.width for i in images), sum(i.height for i in images)), images[0].getpixel((0, 0)))
    y = 0
    for im in images:
        sheet.paste(im, (0, y))
        y += im.height
    return sheet


def cmd_check(args: argparse.Namespace) -> int:
    from rachis.check import check_glyphs

    _load(args)
    names = args.names or None
    problems, notes = check_glyphs(names)
    for line in notes:
        print("note:", line)
    for line in problems:
        print("FAIL:", line)
    print(f"{len(problems)} problems, {len(notes)} notes, {len(names) if names else len(REGISTRY)} glyphs checked")
    return 1 if problems else 0


def cmd_build(args: argparse.Namespace) -> int:
    from rachis.build import build

    out = build(Path(args.out) if args.out else None, statics=not args.no_statics, hint=not args.no_hint)
    for path in sorted(p for p in out.rglob("*") if p.is_file()):
        print(f"{path.stat().st_size:>9}  {path.relative_to(out)}")
    return 0


def cmd_measure(args: argparse.Namespace) -> int:
    from rachis.report import measurements_markdown

    text = measurements_markdown(Path(args.fonts), Path(args.refs) if args.refs else None)
    if args.out:
        Path(args.out).write_text(text)
        print(args.out)
    else:
        print(text)
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    _load(args)
    for s in REGISTRY.values():
        cps = " ".join(f"U+{c:04X}" for c in s.unicodes)
        print(f"{s.name:28} {cps:16} {s.module}")
    print(f"{len(REGISTRY)} glyphs", file=sys.stderr)
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="rachis", description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    def common(sp: argparse.ArgumentParser) -> None:
        sp.add_argument(
            "--draft", action="append", metavar="FILE", help="also load a glyph module from a file; its glyphs win"
        )
        sp.add_argument("--only-drafts", action="store_true", help="do not load the package's own glyph modules")

    pr = sub.add_parser("proof", help="draw glyphs to a PNG")
    common(pr)
    pr.add_argument("--master", default="Regular", help="Light, Regular, Bold, 'Light Italic', Italic or 'Bold Italic'")
    pr.add_argument("--masters", action="store_true", help="draw every master, stacked")
    pr.add_argument(
        "--compare", action="store_true", help="in text mode, add rows set in the reference fonts found in $RACHIS_REFS"
    )
    pr.add_argument("-o", "--out", required=True)
    mode = pr.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--outline", nargs="+", metavar="GLYPH", help="glyph names, or strings of characters, to draw large with points"
    )
    mode.add_argument("--text", nargs="+", metavar="LINE", help="lines of text to set at several sizes")
    pr.add_argument("--sizes", type=int, nargs="+", default=[96, 48, 24, 16, 13])
    pr.add_argument("--scale", type=int, default=3, help="pixel-replicate sizes of 24 px and below by this factor")
    pr.add_argument("--dark", action="store_true")
    pr.add_argument("--all", action="store_true", help="compile every glyph, not only those in the text")
    pr.add_argument("--em", type=int, default=420, help="pixels per em in outline mode")
    pr.add_argument("--columns", type=int, default=4)
    pr.add_argument("--no-points", action="store_true")
    pr.set_defaults(fn=cmd_proof)

    ck = sub.add_parser("check", help="check that glyphs build for every master and that the masters are compatible")
    common(ck)
    ck.add_argument("names", nargs="*", help="glyph names; all when omitted")
    ck.set_defaults(fn=cmd_check)

    bd = sub.add_parser("build", help="build the fonts into fonts/")
    bd.add_argument("--no-statics", action="store_true", help="only the two variable fonts")
    bd.add_argument("--no-hint", action="store_true", help="do not run ttfautohint on the static TrueType fonts")
    bd.add_argument("--out", help="directory to build into (default: fonts/)")
    bd.set_defaults(fn=cmd_build)

    ms = sub.add_parser("measure", help="measure the built fonts, and reference fonts beside them")
    ms.add_argument("--fonts", default="fonts", help="the directory rachis build wrote")
    ms.add_argument("--refs", help="a directory of reference fonts to measure alongside")
    ms.add_argument("-o", "--out", help="write the Markdown here instead of printing it")
    ms.set_defaults(fn=cmd_measure)

    ls = sub.add_parser("list", help="list the registered glyphs")
    common(ls)
    ls.set_defaults(fn=cmd_list)

    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
