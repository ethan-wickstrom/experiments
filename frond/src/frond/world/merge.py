"""Three-way merge, and undo as a revert built on it (design.md "Architecture: worlds").

Undoing what the agent did must not destroy what anyone did since. So undo is a revert: for every path a step
changed, merge3(base = what the step left, ours = what is there now, theirs = what was there before the step).
Lines only the agent changed go back; lines someone else changed since stay; where both touched the same lines,
the path is a conflict, reported and left as it is now.

The line merge is diff3 (Khanna, Kunal and Pierce, "A Formal Investigation of Diff3", 2007): base lines matched in
both versions are stable, and the unstable chunks between them take the side that changed, or conflict when both did.
Matching uses difflib's longest-matching-block search, from the standard library.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from difflib import SequenceMatcher

from frond.world.store import Entry, Worktree


@dataclass(frozen=True, slots=True)
class Merged:
    data: bytes
    conflicts: int  # chunks both sides changed differently; their lines are wrapped in conflict markers


def _matches(base: list[bytes], other: list[bytes]) -> dict[int, int]:
    pairs: dict[int, int] = {}
    for a, b, size in SequenceMatcher(None, base, other, autojunk=False).get_matching_blocks():
        for offset in range(size):
            pairs[a + offset] = b + offset
    return pairs


def merge3(base: bytes, ours: bytes, theirs: bytes) -> Merged:
    """Merge two edits of ``base`` line by line. Binary content merges only when one side left it unchanged."""
    if ours == theirs or theirs == base:
        return Merged(ours, 0)
    if ours == base:
        return Merged(theirs, 0)
    if b"\0" in base or b"\0" in ours or b"\0" in theirs:
        return Merged(ours, 1)
    b_lines, o_lines, t_lines = (x.splitlines(keepends=True) for x in (base, ours, theirs))
    to_ours, to_theirs = _matches(b_lines, o_lines), _matches(b_lines, t_lines)
    out: list[bytes] = []
    conflicts = 0
    i = j = k = 0
    while True:
        stable = next(
            (
                n
                for n in range(i, len(b_lines))
                if n in to_ours and n in to_theirs and to_ours[n] >= j and to_theirs[n] >= k
            ),
            None,
        )
        i2, j2, k2 = (
            (stable, to_ours[stable], to_theirs[stable])
            if stable is not None
            else (
                len(b_lines),
                len(o_lines),
                len(t_lines),
            )
        )
        b_chunk, o_chunk, t_chunk = b_lines[i:i2], o_lines[j:j2], t_lines[k:k2]
        if o_chunk == b_chunk:
            out.extend(t_chunk)
        elif t_chunk == b_chunk or o_chunk == t_chunk:
            out.extend(o_chunk)
        else:
            conflicts += 1
            out.append(b"<<<<<<< now\n")
            out.extend(_terminated(o_chunk))
            out.append(b"=======\n")
            out.extend(_terminated(t_chunk))
            out.append(b">>>>>>> before frond\n")
        if stable is None:
            break
        out.append(b_lines[stable])
        i, j, k = stable + 1, j2 + 1, k2 + 1
    return Merged(b"".join(out), conflicts)


def _terminated(lines: list[bytes]) -> list[bytes]:
    if lines and not lines[-1].endswith(b"\n"):
        return [*lines[:-1], lines[-1] + b"\n"]
    return lines


@dataclass(slots=True)
class Revert:
    """What reverting a step did."""

    restored: list[str] = field(default_factory=list)  # paths put back (fully or line by line)
    conflicts: list[str] = field(default_factory=list)  # paths changed since by someone else, in the same places
    unrestorable: list[str] = field(default_factory=list)  # files too large to have been kept


def revert(work: Worktree, before: str, after: str) -> Revert:
    """Undo the change from tree ``before`` to tree ``after`` in the directory as it is now.

    Only paths that the step changed are touched. Each is merged so that later edits by anyone else survive.
    """
    if not before or not after:  # "" is a snapshot that failed, never a world
        raise ValueError("no world to revert to: a snapshot that failed names none")
    result = Revert()
    current_tree = work.snapshot()
    current = dict(work.store.files(current_tree))
    # removals first, as in checkout: where the step replaced a directory with a file, the file must go before the
    # directory's files come back (F12)
    for change in sorted(work.store.diff(before, after), key=lambda c: c.before is not None):
        path, left, theirs_entry = change.path, change.after, change.before  # left: what the step left
        ours_entry = current.get(path)
        if _same(ours_entry, left):
            # untouched since the step: put the earlier version back exactly
            if theirs_entry is not None and theirs_entry.kind == "large":
                result.unrestorable.append(path)
                continue
            work.apply(path, theirs_entry, ours_entry)
            result.restored.append(path)
            continue
        merged = _merge_entries(work, left, ours_entry, theirs_entry)
        if merged is None:
            result.conflicts.append(path)
            continue
        data, mode = merged
        if data is None:
            work.apply(path, None, ours_entry)
        else:
            entry = Entry("file", work.store.put("blob", data), mode)
            work.apply(path, entry, ours_entry)
        result.restored.append(path)
    for paths in (result.restored, result.conflicts, result.unrestorable):
        paths.sort()  # reported by path, whatever order they were applied in
    return result


def _same(a: Entry | None, b: Entry | None) -> bool:
    if a is None or b is None:
        return a is b
    return a.kind == b.kind and a.oid == b.oid and (a.kind != "file" or a.mode == b.mode)


def _merge_entries(
    work: Worktree, base: Entry | None, ours: Entry | None, theirs: Entry | None
) -> tuple[bytes | None, int] | None:
    """Merge one path's three versions; None when they conflict. A None datum means: remove the path."""
    kinds = {e.kind for e in (base, ours, theirs) if e is not None}
    if kinds - {"file"}:
        return None  # links, directories and large files merge only when untouched since (handled by the caller)
    if ours is None:
        # gone since the step: fine if the step created it (nothing to take back); a conflict if it had existed
        return (None, 0) if theirs is None else None
    base_data = work.read("", base) or b""
    ours_data = work.read("", ours) or b""
    if theirs is None:
        # the step created the file and someone edited it since: removing it would lose their edit
        return None
    merged = merge3(base_data, ours_data, work.read("", theirs) or b"")
    if merged.conflicts:
        return None
    mode = theirs.mode if base is not None and ours.mode == base.mode else ours.mode
    return merged.data, mode
