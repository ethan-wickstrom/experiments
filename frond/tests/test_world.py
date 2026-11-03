"""Worlds: snapshots share structure, checkout restores exactly, and undo is a revert that keeps others' edits."""

from __future__ import annotations

import os
import shutil
import stat
import tempfile
import unittest
from pathlib import Path

from frond.world import Entry, Store, Worktree, merge3, revert


class WorldCase(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="frond-world-"))  # no .git anywhere: worlds don't need it
        self.addCleanup(shutil.rmtree, self.root, True)
        self.store = Store(Path(tempfile.mkdtemp(prefix="frond-store-")))
        self.addCleanup(shutil.rmtree, self.store.root, True)
        self.work = Worktree(self.store, self.root)

    def write(self, path: str, text: str, mode: int | None = None) -> Path:
        p = self.root / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
        if mode is not None:
            os.chmod(p, mode)
        return p

    def state(self) -> dict[str, tuple]:
        """Everything a user could observe about the directory."""
        out: dict[str, tuple] = {}
        for dirpath, dirs, files in os.walk(self.root):
            rel = os.path.relpath(dirpath, self.root)
            for name in dirs + files:
                p = Path(dirpath) / name
                key = os.path.normpath(os.path.join(rel, name))
                if p.is_symlink():
                    out[key] = ("link", os.readlink(p))
                elif p.is_dir():
                    out[key] = ("dir",)
                else:
                    out[key] = ("file", p.read_bytes(), stat.S_IMODE(p.stat().st_mode))
        return out


class SnapshotTest(WorldCase):
    def test_equal_content_is_one_id_and_unchanged_directories_are_shared(self):
        self.write("src/a.py", "a = 1\n")
        self.write("src/deep/b.py", "b = 2\n")
        self.write("docs/readme.md", "hello\n")
        first = self.work.snapshot()
        self.assertEqual(first, self.work.snapshot())
        self.write("src/a.py", "a = 10\n")
        second = self.work.snapshot()
        self.assertNotEqual(first, second)
        self.assertEqual(self.store.tree(first)["docs"], self.store.tree(second)["docs"])
        self.assertEqual(
            self.store.tree(self.store.tree(first)["src"].oid)["deep"],
            self.store.tree(self.store.tree(second)["src"].oid)["deep"],
        )
        self.assertEqual([c.path for c in self.store.diff(first, second)], ["src/a.py"])

    def test_an_edit_that_keeps_size_and_mtime_is_still_seen(self):
        p = self.write("racy.txt", "aaaa")
        before = os.stat(p)
        first = self.work.snapshot()
        p.write_text("bbbb")
        os.utime(p, ns=(before.st_atime_ns, before.st_mtime_ns))  # same size, same mtime, same inode
        self.assertNotEqual(first, self.work.snapshot())


class CheckoutTest(WorldCase):
    def test_round_trip_is_exact_and_caches_are_left_alone(self):
        self.write("keep.txt", "keep\n")
        self.write("edit.txt", "one\ntwo\n")
        self.write("gone.txt", "bye\n")
        self.write("bin/run.sh", "echo hi\n", 0o755)
        self.write("node_modules/pkg/index.js", "cache\n")
        (self.root / "empty").mkdir()
        os.symlink("keep.txt", self.root / "link")
        os.symlink("keep.txt", self.root / "file-to-dir")
        a_state, a = self.state(), self.work.snapshot()

        self.write("edit.txt", "one\nTWO\n")
        (self.root / "gone.txt").unlink()
        self.write("new/deep/file.txt", "new\n")
        os.chmod(self.root / "bin/run.sh", 0o644)
        (self.root / "link").unlink()
        os.symlink("edit.txt", self.root / "link")
        (self.root / "empty").rmdir()
        (self.root / "file-to-dir").unlink()
        self.write("file-to-dir/inner.txt", "now a directory\n")
        self.write("node_modules/pkg/index.js", "cache changed\n")
        b_state, b = self.state(), self.work.snapshot()

        self.work.checkout(a)
        restored = self.state()
        self.assertEqual(
            {k: v for k, v in restored.items() if not k.startswith("node_modules")},
            {k: v for k, v in a_state.items() if not k.startswith("node_modules")},
        )
        self.assertEqual(restored["node_modules/pkg/index.js"][1], b"cache changed\n")  # excluded: untouched
        self.work.checkout(b)
        self.assertEqual(self.state(), b_state)

    def test_an_emptied_directory_comes_back_empty(self):
        self.write("box/item.txt", "x\n")
        full = self.work.snapshot()
        (self.root / "box/item.txt").unlink()
        empty = self.work.snapshot()
        self.work.checkout(full)
        self.work.checkout(empty)
        self.assertTrue((self.root / "box").is_dir())
        self.assertEqual(list((self.root / "box").iterdir()), [])


class Merge3Test(unittest.TestCase):
    base = b"".join(f"line {i}\n".encode() for i in range(1, 11))

    def edit(self, n: int, text: bytes) -> bytes:
        lines = self.base.splitlines(keepends=True)
        lines[n - 1] = text
        return b"".join(lines)

    def test_edits_to_different_lines_both_survive(self):
        ours, theirs = self.edit(2, b"OURS\n"), self.edit(9, b"THEIRS\n")
        merged = merge3(self.base, ours, theirs)
        self.assertEqual(merged.conflicts, 0)
        self.assertIn(b"OURS\n", merged.data)
        self.assertIn(b"THEIRS\n", merged.data)

    def test_the_same_line_changed_two_ways_conflicts(self):
        merged = merge3(self.base, self.edit(5, b"A\n"), self.edit(5, b"B\n"))
        self.assertEqual(merged.conflicts, 1)
        self.assertIn(b"<<<<<<< now\nA\n=======\nB\n>>>>>>> before frond\n", merged.data)

    def test_identical_changes_and_one_sided_changes_merge(self):
        same = self.edit(3, b"X\n")
        self.assertEqual(merge3(self.base, same, same), merge3(self.base, same, self.base))
        self.assertEqual(merge3(self.base, self.base, same).data, same)
        self.assertEqual(merge3(b"", b"", b"new\n").data, b"new\n")

    def test_binary_merges_only_when_one_side_is_unchanged(self):
        base, ours, theirs = b"\0a", b"\0b", b"\0c"
        self.assertEqual(merge3(base, ours, base).data, ours)
        self.assertEqual(merge3(base, ours, theirs).conflicts, 1)


class RevertTest(WorldCase):
    """Undo as a revert: the agent's change goes back; whatever anyone did since stays (requirement R3)."""

    def test_a_later_edit_by_someone_else_survives_the_undo(self):
        text = "".join(f"line {i}\n" for i in range(1, 21))
        self.write("app.py", text)
        before = self.work.snapshot()
        self.write("app.py", text.replace("line 2\n", "line 2 changed by the agent\n"))
        after = self.work.snapshot()
        current = (self.root / "app.py").read_text().replace("line 19\n", "line 19 changed by the user\n")
        self.write("app.py", current)
        result = revert(self.work, before, after)
        self.assertEqual(result.restored, ["app.py"])
        self.assertEqual(result.conflicts, [])
        self.assertEqual((self.root / "app.py").read_text(), text.replace("line 19\n", "line 19 changed by the user\n"))

    def test_the_same_lines_edited_since_is_a_conflict_and_nothing_is_lost(self):
        self.write("a.txt", "x\n")
        before = self.work.snapshot()
        self.write("a.txt", "agent\n")
        after = self.work.snapshot()
        self.write("a.txt", "user\n")
        result = revert(self.work, before, after)
        self.assertEqual(result.conflicts, ["a.txt"])
        self.assertEqual((self.root / "a.txt").read_text(), "user\n")

    def test_creations_deletions_and_modes_go_back(self):
        self.write("old.txt", "old\n")
        self.write("run.sh", "echo\n", 0o755)
        before = self.work.snapshot()
        (self.root / "old.txt").unlink()
        self.write("created/new.txt", "new\n")
        os.chmod(self.root / "run.sh", 0o644)
        after = self.work.snapshot()
        result = revert(self.work, before, after)
        self.assertEqual(sorted(result.restored), ["created/new.txt", "old.txt", "run.sh"])
        self.assertEqual((self.root / "old.txt").read_text(), "old\n")
        self.assertFalse((self.root / "created").exists())
        self.assertEqual(stat.S_IMODE((self.root / "run.sh").stat().st_mode), 0o755)

    def test_a_created_file_someone_edited_since_is_kept(self):
        before = self.work.snapshot()
        self.write("notes.md", "agent\n")
        after = self.work.snapshot()
        self.write("notes.md", "agent\nuser added this\n")
        result = revert(self.work, before, after)
        self.assertEqual(result.conflicts, ["notes.md"])
        self.assertTrue((self.root / "notes.md").exists())

    def test_large_files_are_seen_but_not_kept(self):
        work = Worktree(self.store, self.root, max_blob=8)
        self.write("big.bin", "0123456789")
        before = work.snapshot()
        self.assertEqual(self.store.tree(before)["big.bin"].kind, "large")
        self.write("big.bin", "9876543210x")
        after = work.snapshot()
        self.assertNotEqual(before, after)
        self.assertEqual(revert(work, before, after).unrestorable, ["big.bin"])


class EntryTest(unittest.TestCase):
    def test_entries_are_values(self):
        self.assertEqual(Entry("file", "ab", 0o644), Entry("file", "ab", 0o644))


if __name__ == "__main__":
    unittest.main()
