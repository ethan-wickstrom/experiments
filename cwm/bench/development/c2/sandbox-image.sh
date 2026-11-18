#!/usr/bin/env bash
# Minimal Linux x86_64 image using the already installed Bun executable and libc.
set -euo pipefail
binary=$(readlink -f "$(command -v bun)")
test "$(bun --version)" = 1.4.4
root=$(mktemp -d)
trap 'rm -rf "$root"' EXIT
mkdir -p "$root/bin" "$root/lib/x86_64-linux-gnu" "$root/lib64" "$root/work"
cp "$binary" "$root/bin/bun"
for path in $(ldd "$binary" | awk '$2=="=>" && $3 ~ /^\// {print $3} $1 ~ /^\// {print $1}'); do
  cp -L "$path" "$root$path"
done
tar -C "$root" -cf - . | docker import - cwm-c2-bun:1.4.4
docker run --rm --network none --read-only --user 65534:65534 cwm-c2-bun:1.4.4 /bin/bun --version
