"""Emit the prospectively specified source variants as CWM oracle inputs."""
import json

VARIANTS = {
    "operator position": ("x = x + y;\ny = y - x;", "x = x - y;\ny = y + x;"),
    "operand order": ("y = (x - y) * x;", "y = (y - x) * x;"),
    "assignment destination": ("x = (x + y) * 2;", "y = (x + y) * 2;"),
}


def cases():
    for intervention, variants in VARIANTS.items():
        for args in ([6, 2], [-2, 3]):
            for body in variants:
                source = "export function run(x:number, y:number) {\n" + body + "\nreturn x - y;\n}"
                yield intervention, {"entry": "sample.ts", "fn": "run", "args": args,
                                     "files": {"sample.ts": source}}


if __name__ == "__main__":
    for _, program in cases():
        print(json.dumps(program))
