"""Collect actual Bun observations on trusted authored source. No generated code here."""
import argparse
import gzip
import json
import os
import subprocess
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent


def literals(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def source(lib, settings, behavior, order, eol):
    fn = (f"export function {lib['fn']}({lib['args']}) {{\n"
          + "\n".join("  " + line for line in behavior.split("\n")) + "\n}")
    fields = [fn, *(f"export const {k} = {literals(v)};" for k, v in settings.items())]
    texts = [fields[i] for i in order]
    module = f"// {lib['family']} library\n\n" + "\n\n".join(texts) + "\n"
    return module.replace("\n", eol)


def test_file(lib, assertions):
    lines = ['import { expect, test } from "bun:test";', f'import * as lib from "./{lib["family"]}";',
             'test("library behavior", () => {']
    lines.extend(f"  expect(lib.{expr}).toEqual({literals(val)});" for expr, val in assertions)
    return "\n".join(lines + ["});", ""])


def cases():
    libs = json.loads((HERE / "families.json").read_text())
    for i, lib in enumerate(libs):
        # A fresh family has new code, settings, goals, visible and extra assertions.
        for layout in range(2 if lib["split"] == "train" else 1):
            order = [(i + layout + j) % 3 for j in range(3)]
            if layout:
                order.reverse()
            eol = "\r\n" if i % 5 == 4 and layout else "\n"
            limit, label = lib["limit"], lib["label"]
            old = {limit: i + 2, label: lib["family"] + "-basic"}
            new = {limit: i * 3 + 23, label: lib["family"] + "-plus"}
            for key in (lib["fn"], limit, label):
                for direction in (0, 1):
                    def variant(bit):
                        settings = dict(old)
                        if key in settings and bit:
                            settings[key] = new[key]
                        feature = bit if key == lib["fn"] else 0
                        return settings, feature, source(lib, settings,
                            lib["after" if feature else "before"], order, eol)
                    _, _, before = variant(direction)
                    settings, bit, after = variant(1-direction)
                    if key == lib["fn"]:
                        goal = lib["reverse" if direction else "forward"]
                        expr, expected = f'{key}({lib["call"]})', lib["results"][bit]
                    else:
                        expected = settings[key]
                        expr = key
                        goal = (f"Set {key} to {literals(expected)}." if not layout else
                                f"The exported {key} should now be {literals(expected)}.")
                    check = test_file(lib, [(expr, expected)])
                    extra = test_file(lib, list(settings.items()) +
                                      [(f'{lib["fn"]}({lib["extra"]})', lib["extraResults"][bit])])
                    path = lib["family"] + ".ts"
                    yield dict(family=lib["family"], split=lib["split"], layout=layout, kind=key,
                               direction=direction, goal=goal, path=path, before=before, after=after,
                               check=check, extra=extra, show_observed=bool((i+direction+layout)%2))


def run(folder, name):
    job = subprocess.run(["bun", "test", name], cwd=folder, text=True, capture_output=True,
                         timeout=8, env={**os.environ, "NO_COLOR":"1", "FORCE_COLOR":"0"})
    return {"exit":job.returncode, "stdout":job.stdout, "stderr":job.stderr}


def main(out):
    rows = {"train": [], "holdout": []}
    for row in cases():
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            (folder / "checks.test.ts").write_text(row["check"])
            (folder / "extra.test.ts").write_text(row["extra"])
            path = folder / row["path"]
            path.write_bytes(row["before"].encode())
            before = run(folder, "checks.test.ts")
            path.write_bytes(row["after"].encode())
            after, extra = run(folder, "checks.test.ts"), run(folder, "extra.test.ts")
            if (before["exit"], after["exit"], extra["exit"]) != (1,0,0) or "(fail)" not in before["stderr"]:
                raise ValueError((row["family"],row["kind"],before,after,extra))
            rows[row["split"]].append(dict(**row, observed_before=before, observed_after=after, observed_extra=extra))
    out.mkdir(exist_ok=False)
    for split, records in rows.items():
        raw = "".join(literals(r) + "\n" for r in records).encode()
        (out / f"{split}.jsonl.gz").write_bytes(gzip.compress(raw, mtime=0))
        print(split, len(records), flush=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("out", type=Path)
    main(p.parse_args().out)
