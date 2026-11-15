//! No watched pair of characters is nearer than the committed snapshot, `tests/snapshot/distances.tsv`, records.
//! When a change to a shape is meant to cost a pair some distance, `rachis measure --write` records it and the
//! diff of the snapshot shows the cost.

use std::process::Command;

#[test]
fn no_watched_pair_is_nearer_than_the_snapshot() {
    let out = Command::new(env!("CARGO_BIN_EXE_rachis")).args(["measure", "--check"]).output().expect("rachis runs");
    let report = String::from_utf8_lossy(&out.stdout);
    assert!(out.status.success(), "a pair came nearer:\n{report}{}", String::from_utf8_lossy(&out.stderr));
}
