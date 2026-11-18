"""Serve two-write preferences over NDJSON. All inputs are data; no execution."""
import argparse
import json
import sys

from safetensors.torch import load_file
from encoder import ARMS, HERE, Encoder, comparison, request
from head import FULL, response, score
from provenance import file_hash


class Ranker:
    def __init__(self, arm, method="learned", max_tokens=4096):
        self.arm = arm
        self.method = method
        if method == "learned":
            path = HERE / "weights" / f"{arm}.safetensors"
            pins = json.loads((path.parent / "provenance.json").read_text())
            if file_hash(path) != pins["heads"][arm]:
                raise ValueError("Changed ranker head")
            self.head = load_file(path)
            if set(self.head) != set(FULL):
                raise ValueError("Wrong ranker readout schema")
        self.encoder = Encoder([arm], max_tokens)

    def __call__(self, value):
        state, candidates = request(value)
        if self.method == "comparison":
            ordered = [self.encoder.read(comparison(state, candidates[i], candidates[1-i]),
                                         {}, compare=True)[self.arm]["comparison"] for i in (0, 1)]
            return response(float((ordered[0] - ordered[1]) / 2))
        features = self.encoder.difference(value)[self.arm]
        return response(score(features, self.head))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--serve", action="store_true", help="Persistent NDJSON requests; otherwise read one JSON object")
    p.add_argument("--arm", choices=ARMS, default="C2")
    p.add_argument("--method", choices=["learned", "comparison"], default="learned")
    p.add_argument("--max-tokens", type=int, default=4096, help="Reject longer input; no truncation")
    args = p.parse_args()
    rank = Ranker(args.arm, args.method, args.max_tokens)
    if args.serve:
        for line in sys.stdin:
            try:
                result = rank(json.loads(line))
            except (ValueError, TypeError) as exc:
                result = {"error": str(exc)}
            print(json.dumps(result, allow_nan=False), flush=True)
    else:
        print(json.dumps(rank(json.load(sys.stdin)), allow_nan=False))
