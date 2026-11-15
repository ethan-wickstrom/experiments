//! The outlines of every master agree with the committed snapshot, `tests/snapshot/outlines.sha256`. When a change
//! to the outlines is meant, `rachis digest --write` records it and the diff of the snapshot shows what moved.

use std::process::Command;

#[test]
fn outlines_match_the_snapshot() {
    let out = Command::new(env!("CARGO_BIN_EXE_rachis")).args(["digest", "--check"]).output().expect("rachis runs");
    let report = String::from_utf8_lossy(&out.stdout);
    assert!(out.status.success(), "the outlines changed:\n{report}{}", String::from_utf8_lossy(&out.stderr));
}
