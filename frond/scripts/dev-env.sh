#!/bin/sh
# Start Docker for benchmark runs in a cloud session VM (decision D23), and name the egress CA (decision D27).
#
# The VM ships dockerd but does not run it. Docker Hub rate-limits the VM's shared egress IP (HTTP 429), so pulls
# of Docker Hub images go through Google's public mirror, merged into whatever /etc/docker/daemon.json already holds.
# The VM also re-terminates outbound TLS, so task containers must trust its CA: bench/matrix.py mounts the bundle
# named by FROND_EGRESS_CA (or SSL_CERT_FILE) through bench/compose/egress-ca.yaml.
#
# Harbor runs the agent, the reference solution and the tests through `docker exec`, whose processes inherit the
# umask of the runtime that starts them. dockerd 29 sets its own umask to 0, whatever it is started with, so every
# file they create would be world-writable, and tests that check modes fail for every agent (G26). The default
# runtime here is therefore runc behind a wrapper that sets 022, the umask a standard host gives. Safe to run again.
set -eu
mirror="https://mirror.gcr.io"
runtime=/usr/local/bin/frond-runc
as_root() { if [ "$(id -u)" -eq 0 ]; then "$@"; else sudo "$@"; fi; }
log="${TMPDIR:-/tmp}/dockerd.log"
runc=$(command -v runc)
as_root mkdir -p /etc/docker
printf '#!/bin/sh\n# runc with umask 022 (frond scripts/dev-env.sh, G26)\numask 022\nexec %s "$@"\n' "$runc" |
  as_root tee "$runtime" >/dev/null
as_root chmod 755 "$runtime"
as_root python3 - "$mirror" "$runtime" <<'PY'
import json
import sys
from pathlib import Path

path, mirror, runtime = Path("/etc/docker/daemon.json"), sys.argv[1], sys.argv[2]
text = path.read_text() if path.exists() else ""
config = json.loads(text) if text.strip() else {}
wanted = json.dumps(config, sort_keys=True)
mirrors = config.setdefault("registry-mirrors", [])
if mirror not in mirrors:
    mirrors.append(mirror)
config.setdefault("runtimes", {})["frond-runc"] = {"path": runtime}
config["default-runtime"] = "frond-runc"
if json.dumps(config, sort_keys=True) != wanted:
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
as_root docker info --format 'docker {{.ServerVersion}} ({{.Driver}}, runtime {{.DefaultRuntime}}), mirrors: {{.RegistryConfig.Mirrors}}'
case "$mirrors" in
  *mirror.gcr.io*) ;;
  *) echo "warning: dockerd was already running without $mirror; stop it and run this script again" >&2 ;;
esac
# The probe is bench.matrix.exec_umask in shell, so this script needs nothing but Docker.
probe=mirror.gcr.io/library/alpine:3.20
exec_umask=unknown
if container=$(as_root docker run -d --rm "$probe" sleep 60 2>/dev/null); then
  exec_umask=$(as_root docker exec "$container" sh -c umask 2>/dev/null || echo unknown)
  as_root docker rm -f "$container" >/dev/null 2>&1 || true
fi
if [ "$exec_umask" != "0022" ]; then
  echo "warning: docker exec runs with umask $exec_umask, not 0022; stop dockerd and run this script again (G26)" >&2
fi
ca="${FROND_EGRESS_CA:-${SSL_CERT_FILE:-}}"
if [ -n "$ca" ] && [ -f "$ca" ]; then
  echo "egress CA: $ca (mounted into task containers by bench/matrix.py)"
fi
