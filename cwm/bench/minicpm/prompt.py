"""Prompt the trained MiniCPM5 model directly, or format a next-frame request."""

import argparse
from pathlib import Path

from model import ADAPTER, adapted, generate, load, prompt

parser = argparse.ArgumentParser(description=__doc__)
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument("--text", help="Free-form user message")
group.add_argument("--source", type=Path, help="TypeScript file with a scalar x,y function")
parser.add_argument("--current", help="Observed frame row, e.g. S,2,1,2,3")
parser.add_argument("--adapter", default=ADAPTER, type=Path)
parser.add_argument("--base", action="store_true")
parser.add_argument("--max-new-tokens", type=int, default=32)
args = parser.parse_args()
if bool(args.source) != bool(args.current):
    parser.error("--source and --current go together")
model, tok = load()
if not args.base:
    model = adapted(model, args.adapter)
user = args.text if args.text is not None else prompt(args.source.read_text(), args.current)
print(generate(model, tok, [user], args.max_new_tokens)[0])
