"""Worlds: snapshots share structure, checkout restores exactly, and undo is a revert that keeps others' edits."""

from __future__ import annotations

import json
import os
import shutil
import stat
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

from frond.sessions import SessionStore
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

    def test_a_directory_replaced_by_a_file_comes_back(self):  # F12
        self.write("a/x.txt", "x\n")
        self.write("a/y.txt", "y\n")
        before = self.work.snapshot()
        shutil.rmtree(self.root / "a")
        self.write("a", "replacement\n")
        after = self.work.snapshot()
        result = revert(self.work, before, after)
        self.assertEqual(result.conflicts, [])
        self.assertEqual((self.root / "a" / "x.txt").read_text(), "x\n")
        self.assertEqual(sorted(result.restored), result.restored)  # reported by path
        # and back the other way: a file replaced by a directory
        before, after = after, before
        self.assertEqual(revert(self.work, before, after).conflicts, [])
        self.assertEqual((self.root / "a").read_text(), "replacement\n")

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


class UnreadableTest(WorldCase):
    """A file the snapshot cannot read is kept by its signature, like a large one, and never fails the turn (F13)."""

    def test_an_unreadable_file_is_tracked_not_fatal(self):
        self.write("ok.txt", "fine\n")
        secret = self.write("secret.txt", "root only\n")
        real_open = open

        def guarded(path, *args, **kwargs):
            if str(path) == str(secret):
                raise PermissionError(13, "Permission denied", str(path))
            return real_open(path, *args, **kwargs)

        with mock.patch("builtins.open", side_effect=guarded):
            tree = self.work.snapshot()
        entries = dict(self.store.files(tree))
        self.assertEqual(entries["secret.txt"].kind, "large")
        self.assertEqual(entries["ok.txt"].kind, "file")

    def test_a_failing_snapshot_turns_snapshots_off_with_the_reason(self):
        from frond.world import Timeline

        timeline = Timeline(self.root, self.store.root)
        with mock.patch.object(Worktree, "snapshot", side_effect=OSError(28, "No space left on device")):
            self.assertEqual(timeline.snapshot(), "")
        self.assertFalse(timeline.enabled)
        self.assertIn("No space left on device", timeline.reason)


class CollectionTest(WorldCase):
    """The store sheds what no recent session reaches, and never what a session is still building (ledger G21)."""

    def age(self, oid: str, seconds: float) -> None:
        path = self.store._path(oid)
        then = time.time() - seconds
        os.utime(path, (then, then))

    def test_unreachable_old_objects_go_and_everything_else_stays(self):
        self.write("kept.txt", "kept\n")
        root = self.work.snapshot()
        orphan = self.store.put("blob", b"nobody points here")
        young = self.store.put("blob", b"just written")
        for oid in (root, orphan, *(e.oid for _, e in self.store.files(root))):
            self.age(oid, 7200)
        freed = self.store.sweep(self.store.reachable([root]), older_than=time.time() - 3600)
        self.assertGreater(freed, 0)
        self.assertFalse(self.store._path(orphan).exists())
        self.assertTrue(self.store._path(young).exists())  # too new to collect: a session may be using it
        self.work.checkout(root)  # everything the root needs is still there
        self.assertEqual((self.root / "kept.txt").read_text(), "kept\n")

    def test_an_object_reused_while_the_sweep_runs_stays(self):  # F45
        oid = self.store.put("blob", b"old but about to be reused")
        self.age(oid, 7200)
        real_rename = os.rename

        def reuse_first(src, dst):  # a put() marks the object between the sweep's stat and its rename
            self.store.put("blob", b"old but about to be reused")
            real_rename(src, dst)

        with mock.patch("frond.world.store.os.rename", side_effect=reuse_first):
            self.store.sweep(set(), older_than=time.time() - 3600)
        self.assertEqual(self.store.blob(oid), b"old but about to be reused")

    def test_an_interrupted_sweep_puts_its_objects_back(self):
        oid = self.store.put("blob", b"set aside")
        path = self.store._path(oid)
        os.rename(path, path.with_name(f".gone-{path.name}"))  # as a sweep killed between rename and unlink leaves it
        self.store.sweep(set(), older_than=0)  # nothing is old enough to go
        self.assertEqual(self.store.blob(oid), b"set aside")

    def test_storing_an_object_again_marks_it_in_use(self):
        oid = self.store.put("blob", b"x")
        self.age(oid, 7200)
        self.store.put("blob", b"x")
        self.assertGreater(self.store._path(oid).stat().st_mtime, time.time() - 60)

    def test_sessions_name_their_worlds_and_old_sessions_let_go(self):
        base = Path(tempfile.mkdtemp(prefix="frond-sessions-"))
        self.addCleanup(shutil.rmtree, base, True)
        sessions = SessionStore(self.root, base)
        sessions.directory.mkdir(parents=True)
        (sessions.directory / "a.json").write_text(json.dumps({"turns": [{"world_before": "w1", "world_after": "w2"}]}))
        (sessions.directory / "a.steps.jsonl").write_text(json.dumps({"seq": 1, "world": "w3"}) + "\n")
        old = sessions.directory / "old.json"
        old.write_text(json.dumps({"turns": [{"world_before": "w9", "world_after": "w9"}]}))
        then = time.time() - 40 * 86400
        os.utime(old, (then, then))
        self.assertEqual(sessions.world_roots(), {"w1", "w2", "w3"})
        self.assertEqual(sessions.world_roots(keep=old), {"w1", "w2", "w3", "w9"})  # continued: kept however old (F46)
        first, second = sessions.new_path(), sessions.new_path()
        self.assertNotEqual(first, second)  # /new in the same second gets a file of its own (F1)
        self.assertEqual(sessions.collect(self.store, bound=10**12), 0)  # under the bound: nothing is examined


class EntryTest(unittest.TestCase):
    def test_entries_are_values(self):
        self.assertEqual(Entry("file", "ab", 0o644), Entry("file", "ab", 0o644))


if __name__ == "__main__":
    unittest.main()
