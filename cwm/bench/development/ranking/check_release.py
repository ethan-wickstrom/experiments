"""Exercise the public persistent CLI and compare its scores to the frozen features."""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

import torch
from safetensors.torch import load_file
from build import episodes
from encoder import ARMS, HERE
from head import response, score
from provenance import file_hash


def check(cache):
    if file_hash(cache) != (HERE / "features.sha256").read_text().strip():
        raise ValueError("Ranking cache checksum mismatch")
    row = torch.load(cache, weights_only=True)["records"][0]
    original = episodes()[0][2]
    left, right = original["candidates"]
    inputs = ["{}", *[json.dumps({**original, "candidates": order})
                      for order in ([left, right], [right, left], [left, left])]]
    results = {}
    for arm in ARMS:
        pin = HERE / "weights" / f"{arm}.safetensors"
        expected = response(score(row["features"][arm], load_file(pin)))
        env = {**os.environ, "CWM_THREADS": "8"}
        result = subprocess.run([sys.executable, str(HERE / "rank.py"), "--arm", arm, "--serve"],
                                input="\n".join(inputs) + "\n", capture_output=True, text=True, env=env)
        if result.returncode:
            raise RuntimeError(result.stderr)
        invalid, actual, swapped, tied = map(json.loads, result.stdout.splitlines())
        assert "error" in invalid
        assert actual["choice"] == expected["choice"]
        torch.testing.assert_close(torch.tensor(actual["scores"], dtype=torch.double),
                                   torch.tensor(expected["scores"], dtype=torch.double), atol=1e-6, rtol=1e-6)
        assert swapped["scores"] == actual["scores"][::-1]
        assert tied == {"scores": [0, 0], "choice": None}
        results[arm] = dict(observed_choice=row["choice"], actual=actual, swapped=swapped, identical=tied,
                            expected_from_cache=expected, head_sha256=file_hash(pin))
    return results


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("cache", type=Path)
    args = p.parse_args()
    print(json.dumps(check(args.cache), indent=2))
