"""The glyph programs, one module per group. ``load`` imports them all, which fills ``rachis.glyph.REGISTRY``."""

from __future__ import annotations

import importlib
import importlib.util
import pkgutil
from pathlib import Path

from rachis import glyph as registry


def load() -> None:
    """Import every module of this package."""
    for info in pkgutil.iter_modules(__path__):
        if not info.name.startswith("_"):
            importlib.import_module(f"{__name__}.{info.name}")


def load_file(path: str | Path) -> list[str]:
    """Import a glyph module from a file outside the package (a draft). Its glyphs replace registered ones of the
    same name. Returns the names it defined."""
    path = Path(path)
    spec = importlib.util.spec_from_file_location(f"rachis_draft_{path.stem}", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    before = set(registry.REGISTRY)
    registry.REPLACING = True
    try:
        spec.loader.exec_module(module)
    finally:
        registry.REPLACING = False
    return [n for n, s in registry.REGISTRY.items() if n not in before or s.module == module.__name__]
