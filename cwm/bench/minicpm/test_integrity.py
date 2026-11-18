"""CPU-only integrity tests. No model download, fitting or oracle subprocess."""

import gzip
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import score
import train
from model import DIRECTORY, TRAIN, examples, frame_row, valid_row
from provenance import HELD_SHA, TRAIN_SHA
from score import grade


class IntegrityTest(unittest.TestCase):
    def test_only_complete_authorized_tapes_score(self):
        for path, digest, count in [(TRAIN, TRAIN_SHA, 98), (DIRECTORY / "held.jsonl.gz", HELD_SHA, 34)]:
            data = gzip.decompress(path.read_bytes())
            with tempfile.TemporaryDirectory() as temp:
                tape = Path(temp) / "tape.jsonl"
                tape.write_bytes(data)
                self.assertEqual(len(examples(tape, expected_sha=digest)), count)
                records = data.splitlines(keepends=True)
                changed = json.loads(records[0])
                changed["files"][changed["entry"]] += "\n"
                for bad in (records[:-1], records[::-1], [records[0]] + records, records + [b"\n"],
                            [(json.dumps(changed) + "\n").encode()] + records[1:]):
                    tape.write_bytes(b"".join(bad))
                    with self.assertRaisesRegex(ValueError, "digest"):
                        examples(tape, expected_sha=digest)
                self.assertGreater(len(examples(tape)), 0)

    def test_official_entry_points_require_the_pins_before_model_loading(self):
        with tempfile.TemporaryDirectory() as temp:
            changed = Path(temp) / "changed.jsonl"
            changed.write_bytes(gzip.decompress(TRAIN.read_bytes()).splitlines(keepends=True)[0])
            held = DIRECTORY / "held.jsonl.gz"
            for module, training, argv in [
                (train, changed, ["train", "--out", str(Path(temp) / "new")]),
                (score, changed, ["score", str(held)]),
                (score, TRAIN, ["score", str(changed)]),
            ]:
                with (
                    patch.object(module, "TRAIN", training),
                    patch("sys.argv", argv),
                    patch.object(module, "load") as loader,
                    self.assertRaisesRegex(ValueError, "digest"),
                ):
                    module.main()
                loader.assert_not_called()

    def test_invalid_forecast_never_gets_partial_credit(self):
        target = "S,3,1,7,5"
        for output in ("S,3,1,-0,5", "S,3,1,9007199254740992,5", "S,0,1,7,5",
                       "S,3,-1,7,5", "S,3,1,+7,5", "S,03,1,7,5", "R,3,1,7,5,-0",
                       "S,3,1,7.0,5", "S,3,1,7,５"):
            with self.subTest(output=output):
                counts = grade("S,2,1,4,5", target, output)
                for key in ("valid", "exact", "site_event", "locals", "changed_locals_correct"):
                    self.assertEqual(counts[key], 0)
        self.assertTrue(valid_row("R,1,2,-9007199254740991,9007199254740991,0"))

    def test_oracle_projection_rejects_out_of_domain_fields(self):
        with gzip.open(TRAIN, "rt") as stream:
            record = json.loads(stream.readline())
        f = record["frames"][1]
        entry, fn = record["entry"], record["fn"]
        self.assertTrue(valid_row(frame_row(f, entry, fn)))
        site = f["stack"][0]
        for mapping, key, value in [(site, "line", 0), (site, "column", -1), (site, "column", True),
                                    (f["locals"]["x"], "value", 1 << 53),
                                    (f["locals"]["x"], "value", -0.0)]:
            original = mapping[key]
            mapping[key] = value
            with self.assertRaises(ValueError):
                frame_row(f, entry, fn)
            mapping[key] = original


if __name__ == "__main__":
    unittest.main()
