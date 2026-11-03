"""Streaming field parsing, SUBMIT literal streaming, patches, globs, fuzzy matching, markdown."""

import unittest

from frond.agent.patch import PatchError, apply_chunks, parse_patch
from frond.agent.streaming import FieldStreamParser, SubmitStreamer
from frond.agent.tools import glob_to_regex
from frond.tui.markdown import MarkdownRenderer
from frond.tui.style import make_theme
from frond.tui.text import line_text
from frond.workspace import fuzzy_rank, fuzzy_score

COMPLETION = (
    "[[ ## reasoning ## ]]\nCheck x[0] and [[nested]] brackets.\n\n[[ ## code ## ]]\n```python\nprint(a[1])\n"
    'SUBMIT(response="""Done.\n\nIt\'s \\"fine\\".""")\n```\n\n[[ ## completed ## ]]\n'
)


class FieldStreamParserTest(unittest.TestCase):
    def test_any_chunking_yields_the_same_fields(self):
        for size in (1, 2, 3, 5, 8, 13, 64, len(COMPLETION)):
            fields: dict[str, str] = {}
            parser = FieldStreamParser(lambda f, t, fields=fields: fields.__setitem__(f, fields.get(f, "") + t))
            for i in range(0, len(COMPLETION), size):
                parser.feed(COMPLETION[i : i + size])
            self.assertEqual(fields["reasoning"], "Check x[0] and [[nested]] brackets.", size)
            self.assertTrue(fields["code"].startswith("```python\nprint(a[1])"), size)
            self.assertTrue(fields["code"].endswith("```"), size)
            self.assertNotIn("completed", fields)


class SubmitStreamerTest(unittest.TestCase):
    def stream(self, code: str, size: int = 1) -> str:
        out: list[str] = []
        s = SubmitStreamer(out.append)
        for i in range(0, len(code), size):
            s.feed(code[i : i + size])
        return "".join(out)

    def test_decodes_triple_quoted_literal(self):
        code = '```python\nSUBMIT(response="""Done.\n\nIt\'s \\"fine\\".""")\n```'
        for size in (1, 2, 7, 1000):
            self.assertEqual(self.stream(code, size), 'Done.\n\nIt\'s "fine".')

    def test_positional_and_single_quotes(self):
        self.assertEqual(self.stream("# wrap up\nSUBMIT('a\\nb')"), "a\nb")
        self.assertEqual(self.stream('SUBMIT(response="")'), "")

    def test_ignores_computed_or_late_submits(self):
        self.assertEqual(self.stream("SUBMIT(response=summary)"), "")
        self.assertEqual(self.stream("x = 1\nSUBMIT(response='hi')"), "")


class PatchTest(unittest.TestCase):
    def test_envelope_update_with_anchor_and_whitespace_drift(self):
        original = "class A:\n    def f(self):\n        return 1   \n\nclass B:\n    def f(self):\n        return 1\n"
        patch = (
            "*** Begin Patch\n*** Update File: m.py\n@@ class B:\n     def f(self):\n-        return 1\n"
            "+        return 2\n*** End Patch"
        )
        [op] = parse_patch(patch)
        self.assertEqual(apply_chunks(original, op.chunks, "m.py").splitlines()[-1], "        return 2")
        self.assertIn("return 1   ", apply_chunks(original, op.chunks, "m.py"))

    def test_add_delete_move(self):
        ops = parse_patch(
            "*** Begin Patch\n*** Add File: new.txt\n+hello\n*** Delete File: old.txt\n"
            "*** Update File: a.py\n*** Move to: b.py\n@@\n-x = 1\n+x = 2\n*** End Patch"
        )
        self.assertEqual(
            [(o.kind, o.path, o.move_to) for o in ops],
            [("add", "new.txt", None), ("delete", "old.txt", None), ("update", "a.py", "b.py")],
        )
        self.assertEqual(ops[0].content, "hello\n")

    def test_unified_diff(self):
        diff = "--- a/f.txt\n+++ b/f.txt\n@@ -1,3 +1,3 @@\n one\n-two\n+TWO\n three\n"
        [op] = parse_patch(diff)
        self.assertEqual(apply_chunks("one\ntwo\nthree\n", op.chunks, "f.txt"), "one\nTWO\nthree\n")

    def test_missing_context_is_reported(self):
        [op] = parse_patch("*** Begin Patch\n*** Update File: f\n@@\n-nope\n+yes\n*** End Patch")
        with self.assertRaises(PatchError):
            apply_chunks("something else\n", op.chunks, "f")


class GlobAndFuzzyTest(unittest.TestCase):
    def test_glob(self):
        self.assertTrue(glob_to_regex("**/*.py").match("a/b/c.py"))
        self.assertTrue(glob_to_regex("**/*.py").match("c.py"))
        self.assertFalse(glob_to_regex("*.py").match("a/c.py"))
        self.assertTrue(glob_to_regex("src/**/test_*.{ts,tsx}").match("src/x/y/test_a.tsx"))
        self.assertTrue(glob_to_regex("[!a]b").match("cb"))

    def test_fuzzy_prefers_basename_and_boundaries(self):
        files = ["docs/client.md", "src/frond/cli.py", "src/frond/tui/app.py", "tests/test_cli.py"]
        self.assertEqual(fuzzy_rank("cli", files)[0], "src/frond/cli.py")
        self.assertIsNone(fuzzy_score("zzz", "src/app.py"))
        self.assertEqual(fuzzy_rank("tuiapp", files)[0], "src/frond/tui/app.py")


class MarkdownTest(unittest.TestCase):
    def test_blocks_and_inline(self):
        md = MarkdownRenderer(make_theme(), lambda ref: "file:///" + ref)
        text = "# Title\n\nSome **bold** and `code.py:3`.\n\n- one\n  - two\n1. first\n\n```py\nx = 1\n```\n> quote"
        lines = [line_text(line) for line in md.render(text, 40)]
        self.assertIn("Title", lines)
        self.assertIn("Some bold and code.py:3.", lines)
        self.assertIn("• one", lines)
        self.assertIn("  ◦ two", lines)
        self.assertIn("│ quote", lines)
        self.assertTrue(any(line.startswith(" x = 1") for line in lines))
        links = [s.style.link for line in md.render("see `code.py:3`", 40) for s in line if s.style.link]
        self.assertEqual(links, ["file:///code.py:3"])


if __name__ == "__main__":
    unittest.main()
