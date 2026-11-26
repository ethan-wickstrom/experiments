import tempfile
import unittest
from pathlib import Path

import verdict


class Record(unittest.TestCase):
    def setUp(self) -> None:
        self.path = Path(tempfile.mkdtemp()) / "bets.jsonl"

    def run_cli(self, *args: str) -> int:
        return verdict.main(["--record", str(self.path), *args])

    def test_scores_resolved_bets_and_lists_overdue_ones(self) -> None:
        self.assertEqual(self.run_cli("bet", "a", "0.9", "2000-01-01", "x", "--decided-by", "d"), 0)
        self.assertEqual(self.run_cli("bet", "b", "0.1", "2000-01-01", "y", "--decided-by", "d"), 0)
        self.assertEqual(self.run_cli("verdict", "a", "no", "--evidence", "e"), 0)
        text = verdict.score(*verdict.load(self.path), "2026-01-01")
        self.assertIn("Brier score 0.810", text)
        self.assertIn("overdue: b", text)
        self.assertNotIn("overdue: a", text)

    def test_a_probability_on_a_bin_edge_is_counted_once_and_a_compact_date_is_stored_in_full(self) -> None:
        self.run_cli("bet", "a", "0.6", "20000101", "x", "--decided-by", "d")
        self.run_cli("verdict", "a", "yes", "--evidence", "e")
        self.run_cli("bet", "b", "0.5", "20000101", "x", "--decided-by", "d")
        text = verdict.score(*verdict.load(self.path), "2026-01-01")
        self.assertIn("60%-80%  1  100%", text)
        self.assertNotIn("40%-60%", text)
        self.assertIn("overdue: b (due 2000-01-01)", text)

    def test_refuses_a_second_verdict_and_leaves_the_record_unchanged(self) -> None:
        self.run_cli("bet", "a", "0.5", "2000-01-01", "x", "--decided-by", "d")
        self.run_cli("verdict", "a", "yes", "--evidence", "e")
        before = self.path.read_text()
        self.assertEqual(self.run_cli("verdict", "a", "no", "--evidence", "e"), 1)
        self.assertEqual(self.run_cli("verdict", "zz", "no", "--evidence", "e"), 1)
        self.assertEqual(self.run_cli("bet", "c", "1.0", "2000-01-01", "x", "--decided-by", "d"), 1)
        self.assertEqual(self.path.read_text(), before)

    def test_the_committed_record_loads(self) -> None:
        verdict.load(verdict.RECORD)


if __name__ == "__main__":
    unittest.main()
