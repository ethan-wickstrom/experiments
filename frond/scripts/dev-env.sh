#!/bin/sh
# Start Docker for benchmark runs in a cloud session VM (decision D23).
#
# The VM ships dockerd but does not run it. Docker Hub rate-limits the VM's shared egress IP (HTTP 429), so pulls
# of Docker Hub images go through Google's public mirror. Safe to run again: it does nothing when Docker is up.
set -eu
log="${TMPDIR:-/tmp}/dockerd.log"
if ! docker info >/dev/null 2>&1; then
  mkdir -p /etc/docker
  if [ ! -f /etc/docker/daemon.json ]; then
    printf '{\n  "registry-mirrors": ["https://mirror.gcr.io"]\n}\n' > /etc/docker/daemon.json
  fi
  nohup dockerd > "$log" 2>&1 &
  tries=0
  until docker info >/dev/null 2>&1; do
    tries=$((tries + 1))
    if [ "$tries" -gt 60 ]; then
      echo "dockerd did not start; see $log" >&2
      exit 1
    fi
    sleep 0.5
  done
fi
docker info --format 'docker {{.ServerVersion}} ({{.Driver}}), mirrors: {{.RegistryConfig.Mirrors}}'
