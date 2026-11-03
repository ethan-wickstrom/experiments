#!/bin/sh
# Start Docker for benchmark runs in a cloud session VM (decision D23), and name the egress CA (decision D27).
#
# The VM ships dockerd but does not run it. Docker Hub rate-limits the VM's shared egress IP (HTTP 429), so pulls
# of Docker Hub images go through Google's public mirror, merged into whatever /etc/docker/daemon.json already holds.
# The VM also re-terminates outbound TLS, so task containers must trust its CA: bench/matrix.py mounts the bundle
# named by FROND_EGRESS_CA (or SSL_CERT_FILE) through bench/compose/egress-ca.yaml. Safe to run again.
set -eu
mirror="https://mirror.gcr.io"
as_root() { if [ "$(id -u)" -eq 0 ]; then "$@"; else sudo "$@"; fi; }
log="${TMPDIR:-/tmp}/dockerd.log"
as_root mkdir -p /etc/docker
as_root python3 - "$mirror" <<'PY'
import json
import sys
from pathlib import Path

path, mirror = Path("/etc/docker/daemon.json"), sys.argv[1]
text = path.read_text() if path.exists() else ""
config = json.loads(text) if text.strip() else {}
mirrors = config.setdefault("registry-mirrors", [])
if mirror not in mirrors:
    mirrors.append(mirror)
    path.write_text(json.dumps(config, indent=2) + "\n")
PY
if ! as_root docker info >/dev/null 2>&1; then
  as_root sh -c "nohup dockerd > '$log' 2>&1 &"
  tries=0
  until as_root docker info >/dev/null 2>&1; do
    tries=$((tries + 1))
    if [ "$tries" -gt 60 ]; then
      echo "dockerd did not start; see $log" >&2
      exit 1
    fi
    sleep 0.5
  done
fi
mirrors=$(as_root docker info --format '{{.RegistryConfig.Mirrors}}')
as_root docker info --format 'docker {{.ServerVersion}} ({{.Driver}}), mirrors: {{.RegistryConfig.Mirrors}}'
case "$mirrors" in
  *mirror.gcr.io*) ;;
  *) echo "warning: dockerd was already running without $mirror; restart it to use the mirror" >&2 ;;
esac
ca="${FROND_EGRESS_CA:-${SSL_CERT_FILE:-}}"
if [ -n "$ca" ] && [ -f "$ca" ]; then
  echo "egress CA: $ca (mounted into task containers by bench/matrix.py)"
fi
