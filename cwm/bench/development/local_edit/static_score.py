"""Type-check the frozen references and completed edits together with both Bun checks."""
import gzip
import json
import subprocess
import tempfile
from pathlib import Path

from wire import splice

HERE = Path(__file__).resolve().parent
MODULES = HERE.parents[2] / "node_modules"


def check(episode, text):
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        (root / "node_modules").symlink_to(MODULES, target_is_directory=True)
        for name, body in [(episode["path"], text), ("checks.test.ts", episode["check"]),
                           ("accept.test.ts", episode["extra"])]:
            (root / name).write_bytes(body.encode())
        config = {
            "compilerOptions": {
                "strict": True, "skipLibCheck": True, "target": "esnext",
                "module": "preserve", "types": ["bun"], "noEmit": True,
            },
            "files": [episode["path"], "checks.test.ts", "accept.test.ts"],
        }
        (root / "tsconfig.json").write_text(json.dumps(config))
        job = subprocess.run([MODULES / ".bin/tsc", "-p", ".", "--pretty", "false"],
                             cwd=root, text=True, stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, timeout=30)
        if job.returncode and "error TS" not in job.stdout:
            raise RuntimeError(job.stdout)
        return {"exit": job.returncode, "diagnostics": job.stdout.rstrip()}


def evaluate():
    data = HERE / "data"
    with gzip.open(data / "holdout.jsonl.gz", "rt") as tape:
        episodes = [json.loads(line) for line in tape]
    for ep in episodes:
        reference = check(ep, ep["after"])
        if reference["exit"]:
            raise ValueError((ep["family"], ep["goal"], reference))
    results = []
    for arm in ("base", "trained", "edit-only"):
        scores = json.loads(gzip.decompress((data / f"score-{arm}.json.gz").read_bytes()))
        assert scores["arm"] == arm
        for ep, row in zip(episodes, scores["outputs"], strict=True):
            assert (ep["family"], ep["goal"]) == (row["family"], row["goal"])
            answer = row["prediction"]
            compiler = None
            if answer["stopped"]:
                text = splice(ep["before"], answer["start"], answer["end"], answer["replacement"])
                assert text == answer["text"]
                compiler = check(ep, text)
            results.append({
                "arm": arm,
                "family": ep["family"],
                "goal": ep["goal"],
                "both": row.get("visible", {}).get("passed", False) and row.get("extra", {}).get("passed", False),
                "compiler": compiler,
            })
    return results


if __name__ == "__main__":
    print(json.dumps(evaluate(), ensure_ascii=False, separators=(",", ":")))
