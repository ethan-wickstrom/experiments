"""``frond --demo``: a scripted session in a throwaway sample project, so the TUI can be tried without an API key.

The model is scripted, but everything it does is real: the REPL runs the code, files are edited, and the tests
really run. The sample project lives in a fresh temporary directory.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from frond.agent.scripted import ScriptedEngine, Step

PROJECT = {
    "README.md": "# wordcount\n\nCounts the words in its input.\n\n    echo 'a b c' | python3 wordcount.py\n",
    "wordcount.py": '''"""Count words in text read from stdin."""

import sys


def count_words(text: str) -> int:
    return len(text.split())


def main() -> None:
    print(count_words(sys.stdin.read()))


if __name__ == "__main__":
    main()
''',
    "test_wordcount.py": """import unittest

from wordcount import count_words


class CountWordsTest(unittest.TestCase):
    def test_counts_words(self):
        self.assertEqual(count_words("the quick brown fox"), 4)

    def test_empty(self):
        self.assertEqual(count_words(""), 0)


if __name__ == "__main__":
    unittest.main()
""",
}

SUGGESTION = "add a --unique flag that counts distinct words, ignoring case, with tests"

_PLAN = [
    "Read wordcount.py and its tests",
    "Add count_unique() and a --unique flag",
    "Cover the new behaviour with tests",
    "Run the suite and try the flag",
]


def _plan(done: int) -> str:
    rows = [f"[x] {s}" if i < done else f"[>] {s}" if i == done else f"[ ] {s}" for i, s in enumerate(_PLAN)]
    return "plan([\n" + "".join(f"    {r!r},\n" for r in rows) + "])"


_TEST_FILE = """import subprocess
import sys
import unittest

from wordcount import count_unique


class CountUniqueTest(unittest.TestCase):
    def test_ignores_case_and_repeats(self):
        self.assertEqual(count_unique("The cat saw the CAT"), 3)

    def test_empty(self):
        self.assertEqual(count_unique(""), 0)

    def test_cli_flag(self):
        result = subprocess.run(
            [sys.executable, "wordcount.py", "--unique"], input="a A b", capture_output=True, text=True, check=True
        )
        self.assertEqual(result.stdout.strip(), "2")


if __name__ == "__main__":
    unittest.main()
"""

STEPS = [
    Step(
        "I'll start with the layout, then have sub-queries summarise each Python file in parallel so I know what "
        "I'm working with before reading anything closely.",
        """print(ls())
files = glob("*.py")
summaries = llm_query_batched([f"In one line, what does this file do?\\n\\n{read(f)}" for f in files])
for name, line in zip(files, summaries):
    print(f"{name}: {line}")
print(view("wordcount.py"))""",
    ),
    Step(
        "A single module with unittest tests. Before changing anything, I'll run the suite to get a baseline.",
        'print(sh("python3 -m unittest -v"))',
    ),
    Step(
        "The baseline is green (2 tests). I'll lay out the plan, then add count_unique() next to count_words() and "
        "teach main() a --unique flag.",
        _plan(1)
        + """
print(edit(
    "wordcount.py",
    "def count_words(text: str) -> int:\\n    return len(text.split())\\n",
    "def count_words(text: str) -> int:\\n    return len(text.split())\\n\\n\\n"
    "def count_unique(text: str) -> int:\\n"
    '    \\"\\"\\"Count distinct words, ignoring case.\\"\\"\\"\\n'
    "    return len({word.casefold() for word in text.split()})\\n",
))
print(edit(
    "wordcount.py",
    "def main() -> None:\\n    print(count_words(sys.stdin.read()))\\n",
    "def main() -> None:\\n"
    "    text = sys.stdin.read()\\n"
    '    unique = "--unique" in sys.argv[1:]\\n'
    "    print(count_unique(text) if unique else count_words(text))\\n",
))""",
    ),
    Step(
        "Now tests for the new behaviour, in their own file so the existing suite stays untouched. One of them runs "
        "the CLI end to end.",
        _plan(2) + f"\nprint(write('test_unique.py', {_TEST_FILE!r}))",
    ),
    Step(
        "Run the whole suite, then try the flag by hand on a sample with repeated, mixed-case words.",
        _plan(3)
        + """
r = sh("python3 -m unittest -v")
print(r.output[-600:])
print(sh("printf 'one two two Three three THREE' | python3 wordcount.py --unique"))""",
    ),
    Step(
        "All 5 tests pass and the flag reports 3 distinct words for the sample, as expected. Time to report back.",
        'SUBMIT(response="""Added a `--unique` flag that counts distinct words, ignoring case.\n\n'
        "- `wordcount.py:10` adds `count_unique()`, and `main()` switches on `--unique`\n"
        "- `test_unique.py` adds 3 tests, including an end-to-end run of the flag\n\n"
        "Verified with `python3 -m unittest -v` (**5 passed**), and "
        '`printf \'one two two Three three THREE\' | python3 wordcount.py --unique` prints `3`.""")',
    ),
]

AFTER = Step(
    "This is the scripted demo, so there is nothing more I can do with a new request.",
    'SUBMIT(response="""That was frond\'s **scripted demo**: the model\'s replies were canned, but the code, edits '
    "and test runs were real.\n\nTo use frond on your own code, set an API key (for example `ANTHROPIC_API_KEY`) "
    'and run `frond` in your project, or pass `--model provider/name`."""\n)',
)


def _sub_answer(prompt: str) -> str:
    if "unittest" in prompt:
        return "Unit tests for count_words(): a normal sentence and the empty string."
    if "def count_words" in prompt:
        return "Defines count_words() and a CLI entry point that prints the word count of stdin."
    return "A short file."


def make_project() -> Path:
    root = Path(tempfile.mkdtemp(prefix="frond-demo-"))
    for name, text in PROJECT.items():
        (root / name).write_text(text)
    return root


def make_engine(*, delay: float = 0.012, chunk: int = 6) -> ScriptedEngine:
    return ScriptedEngine(
        list(STEPS), chunk=chunk, delay=delay, sub_answer=_sub_answer, after_script=lambda _text: AFTER
    )
