"""Run one command so that it cannot change the filesystem: the shell of frond's read-only agents.

    python -I _sandbox.py TMPDIR -- ARGV...

This runs as a fresh, single-threaded process that holds nothing but stdio. Before exec'ing ARGV it applies
the strongest restriction the system allows, then checks that the working directory really is unwritable.

1. Linux with unprivileged user namespaces. It makes new user, mount and network namespaces and sets every
   mount read-only with one recursive ``mount_setattr``. Every kind of write then fails with EROFS, including
   chmod, chown, utime and xattrs. There is no network, and abstract sockets are out of reach.
   - Fresh tmpfs mounts hide /run (docker, D-Bus and user-session sockets) and /tmp (tmux, X11 and ssh-agent
     sockets); /tmp is left alone when the workspace lives under it.
   - TMPDIR becomes a private tmpfs.
   - Inside, the command runs with a non-zero uid, so exec drops the capabilities that could remount anything
     read-write.
2. Linux without user namespaces (for example Ubuntu's AppArmor restriction). It uses Landlock, ABI 3 or
   later: reads and execution everywhere, writes only in TMPDIR, /dev/null and the tty, and no TCP from ABI 4.
   Landlock cannot restrict chmod, chown, utime, xattrs or connecting to an existing UNIX socket.
3. macOS. It uses Seatbelt (sandbox-exec) with a deny-by-default profile that allows reads and writes only to
   temporary directories, /dev/null and the tty. This path follows the profiles of Codex and Anthropic's
   sandbox-runtime and has not been run on macOS here.

When none of these can be applied, or the check fails, it prints "frond-sandbox: ..." and exits 125 without
running anything. FROND_SANDBOX=namespaces|landlock|none limits the choice (for tests).
"""

from __future__ import annotations

import ctypes
import fcntl
import os
import socket
import struct
import sys

UNAVAILABLE = 125


class Unavailable(Exception):
    pass


def _libc() -> ctypes.CDLL:
    libc = ctypes.CDLL(None, use_errno=True)
    libc.syscall.restype = ctypes.c_long
    return libc


def _check(result: int, what: str) -> None:
    if result < 0:
        errno = ctypes.get_errno()
        raise Unavailable(f"{what}: {os.strerror(errno)}")


# ── Linux: a read-only mount namespace ───────────────────────────────────────

SYS_MOUNT_SETATTR = 442  # the same number on x86_64 and aarch64 (kernel 5.12+)
AT_FDCWD, AT_RECURSIVE, MOUNT_ATTR_RDONLY = -100, 0x8000, 0x1
MS_NOSUID, MS_NODEV, MS_PRIVATE = 0x2, 0x4, 1 << 18


class _MountAttr(ctypes.Structure):
    _fields_ = (
        ("attr_set", ctypes.c_uint64),
        ("attr_clr", ctypes.c_uint64),
        ("propagation", ctypes.c_uint64),
        ("userns_fd", ctypes.c_uint64),
    )


def namespaces(tmpdir: str) -> str:
    libc = _libc()
    uid, gid = os.getuid(), os.getgid()
    cwd = os.getcwd()
    try:
        os.unshare(os.CLONE_NEWUSER | os.CLONE_NEWNS | os.CLONE_NEWNET)
        for path, text in (
            ("/proc/self/setgroups", "deny"),
            # never uid 0 inside: exec then drops the capabilities that could undo the read-only mounts
            ("/proc/self/uid_map", f"{uid or 1} {uid} 1"),
            ("/proc/self/gid_map", f"{gid or 1} {gid} 1"),
        ):
            with open(path, "w") as f:
                f.write(text)
    except OSError as exc:
        raise Unavailable(f"user namespaces: {exc.strerror or exc}") from None
    attr = _MountAttr(MOUNT_ATTR_RDONLY, 0, MS_PRIVATE, 0)
    _check(
        libc.syscall(
            SYS_MOUNT_SETATTR,
            ctypes.c_int(AT_FDCWD),
            b"/",
            ctypes.c_uint(AT_RECURSIVE),
            ctypes.byref(attr),
            ctypes.c_size_t(ctypes.sizeof(attr)),
        ),
        "mount_setattr",
    )

    def tmpfs(target: str, mode: str) -> bool:
        flags = ctypes.c_ulong(MS_NOSUID | MS_NODEV)
        return libc.mount(b"tmpfs", target.encode(), b"tmpfs", flags, f"mode={mode}".encode()) == 0

    if os.path.isdir("/run"):
        tmpfs("/run", "0755")
    fresh_tmp = not _under(cwd, "/tmp") and os.path.isdir("/tmp") and tmpfs("/tmp", "1777")
    if fresh_tmp and _under(tmpdir, "/tmp"):
        os.makedirs(tmpdir, mode=0o700, exist_ok=True)  # inside the new, writable /tmp
    elif not tmpfs(tmpdir, "0700"):
        raise Unavailable(f"private tmpfs: {os.strerror(ctypes.get_errno())}")
    _loopback_up()  # the new network namespace has only a loopback device, and it starts down
    return "namespaces"


def _loopback_up() -> None:
    siocgifflags, siocsifflags, iff_up = 0x8913, 0x8914, 0x1
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            request = struct.pack("16sH14s", b"lo", 0, b"")
            flags = struct.unpack("16sH14s", fcntl.ioctl(s, siocgifflags, request))[1]
            fcntl.ioctl(s, siocsifflags, struct.pack("16sH14s", b"lo", flags | iff_up, b""))
    except OSError:
        pass  # local servers will not work, everything else does


def _under(path: str, parent: str) -> bool:
    return path == parent or path.startswith(parent.rstrip("/") + "/")


# ── Linux: Landlock ──────────────────────────────────────────────────────────

SYS_CREATE_RULESET, SYS_ADD_RULE, SYS_RESTRICT_SELF = 444, 445, 446  # x86_64 and aarch64
CREATE_RULESET_VERSION, RULE_PATH_BENEATH, PR_SET_NO_NEW_PRIVS = 1, 1, 38
EXECUTE, WRITE_FILE, READ_FILE, READ_DIR = 1 << 0, 1 << 1, 1 << 2, 1 << 3
REFER, TRUNCATE, IOCTL_DEV = 1 << 13, 1 << 14, 1 << 15  # ABI 2, 3 and 5
NET_ALL = 0b11  # bind and connect over TCP, ABI 4
SCOPE_ALL = 0b11  # abstract UNIX sockets and signals outside the sandbox, ABI 6


class _RulesetAttr(ctypes.Structure):
    _fields_ = (
        ("handled_access_fs", ctypes.c_uint64),
        ("handled_access_net", ctypes.c_uint64),
        ("scoped", ctypes.c_uint64),
    )


class _PathBeneath(ctypes.Structure):
    _pack_ = 1
    _fields_ = (("allowed_access", ctypes.c_uint64), ("parent_fd", ctypes.c_int32))


def landlock(tmpdir: str) -> str:
    libc = _libc()
    abi = libc.syscall(SYS_CREATE_RULESET, None, ctypes.c_size_t(0), ctypes.c_uint32(CREATE_RULESET_VERSION))
    if abi < 3:  # below ABI 3, truncation is not covered and a "read-only" file can still be emptied
        raise Unavailable("Landlock ABI 3 or later is needed" if abi > 0 else "Landlock is not enabled")
    handled = (1 << 13) - 1 | REFER | TRUNCATE | (IOCTL_DEV if abi >= 5 else 0)
    attr = _RulesetAttr(handled, NET_ALL if abi >= 4 else 0, SCOPE_ALL if abi >= 6 else 0)
    ruleset = libc.syscall(SYS_CREATE_RULESET, ctypes.byref(attr), ctypes.c_size_t(ctypes.sizeof(attr)), 0)
    _check(ruleset, "landlock_create_ruleset")
    file_rights = (READ_FILE | WRITE_FILE | TRUNCATE | IOCTL_DEV) & handled
    rules = [("/", EXECUTE | READ_FILE | READ_DIR), (tmpdir, handled), ("/dev/null", file_rights)]
    rules.append(("/dev/tty", file_rights))
    for path, access in rules:
        try:
            fd = os.open(path, os.O_PATH | os.O_CLOEXEC)
        except OSError:
            continue  # e.g. no controlling terminal
        try:
            rule = _PathBeneath(access, fd)
            _check(libc.syscall(SYS_ADD_RULE, ruleset, RULE_PATH_BENEATH, ctypes.byref(rule), 0), "landlock_add_rule")
        finally:
            os.close(fd)
    _check(libc.prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0), "no_new_privs")
    _check(libc.syscall(SYS_RESTRICT_SELF, ruleset, 0), "landlock_restrict_self")
    os.close(ruleset)
    return "landlock"


# ── macOS: Seatbelt ──────────────────────────────────────────────────────────

SEATBELT_PROFILE = """\
(version 1)
(deny default)
(allow process-exec)
(allow process-fork)
(allow signal (target same-sandbox))
(allow process-info* (target same-sandbox))
(allow sysctl-read)
(allow mach-lookup (global-name "com.apple.system.opendirectoryd.libinfo"))
(allow ipc-posix-sem)
(allow pseudo-tty)
(allow file-read*)
(allow file-ioctl (literal "/dev/null") (literal "/dev/tty") (regex #"^/dev/ttys[0-9]+$"))
(allow file-write* (literal "/dev/null") (literal "/dev/tty")
  (subpath "/private/tmp") (subpath "/private/var/folders") (subpath (param "TMPDIR")))
(deny system-fcntl (fcntl-command 80 110))
"""


def seatbelt(tmpdir: str, argv: list[str]) -> list[str]:
    tool = "/usr/bin/sandbox-exec"
    if not os.access(tool, os.X_OK):
        raise Unavailable("sandbox-exec is not available")
    return [tool, "-p", SEATBELT_PROFILE, f"-DTMPDIR={os.path.realpath(tmpdir)}", "--", *argv]


# ── putting it together ──────────────────────────────────────────────────────


def confine(tmpdir: str, argv: list[str], choice: str) -> tuple[str, list[str]]:
    """Apply a sandbox to this process; returns its name and the argv to exec."""
    if sys.platform == "darwin" and choice in ("", "seatbelt"):
        return "seatbelt", seatbelt(tmpdir, argv)
    if not sys.platform.startswith("linux"):
        raise Unavailable(f"no sandbox for {sys.platform}")
    reasons = []
    for name, apply in (("namespaces", namespaces), ("landlock", landlock)):
        if choice not in ("", name):
            continue
        try:
            return apply(tmpdir), argv
        except Unavailable as exc:
            reasons.append(f"{name}: {exc}")
    raise Unavailable("; ".join(reasons) or f"FROND_SANDBOX={choice} is not available")


def verify(name: str) -> None:
    """The working directory must not be writable any more, or nothing runs."""
    if name == "seatbelt":
        return  # applied by sandbox-exec at exec time, after this process is gone
    probe = os.path.join(os.getcwd(), f".frond-sandbox-check-{os.getpid()}")
    try:
        fd = os.open(probe, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except OSError:
        return
    os.close(fd)
    os.unlink(probe)
    raise Unavailable(f"the {name} sandbox did not take effect")


def main() -> None:
    if len(sys.argv) < 4 or sys.argv[2] != "--":
        sys.stderr.write("usage: _sandbox.py TMPDIR -- ARGV...\n")
        os._exit(2)
    tmpdir, argv = sys.argv[1], sys.argv[3:]
    choice = os.environ.pop("FROND_SANDBOX", "")
    try:
        if choice == "none":
            raise Unavailable("disabled by FROND_SANDBOX=none")
        name, argv = confine(tmpdir, argv, choice)
        verify(name)
    except Unavailable as exc:
        sys.stderr.write(f"frond-sandbox: no read-only sandbox is available here ({exc})\n")
        sys.stderr.flush()
        os._exit(UNAVAILABLE)
    cache = os.path.join(tmpdir, ".cache")
    os.environ.update(
        TMPDIR=tmpdir,
        XDG_CACHE_HOME=cache,
        PYTHONDONTWRITEBYTECODE="1",
        PYTEST_ADDOPTS=(os.environ.get("PYTEST_ADDOPTS", "") + " -p no:cacheprovider").strip(),
        FROND_SANDBOXED=name,
    )
    try:
        os.execvp(argv[0], argv)
    except OSError as exc:
        sys.stderr.write(f"frond-sandbox: cannot run {argv[0]}: {exc.strerror}\n")
        os._exit(127)


if __name__ == "__main__":
    main()
