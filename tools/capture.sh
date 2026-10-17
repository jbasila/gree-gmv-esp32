#!/usr/bin/env bash
# Capture sniffer serial log to captures/<name>.log for N seconds.
# usage: tools/capture.sh <name> <seconds> [device]
set -euo pipefail
name=${1:?name}; secs=${2:?seconds}; dev=${3:-/dev/cu.usbserial-0001}
out="$(dirname "$0")/../captures/${name}.log"
echo "capturing ${secs}s -> ${out}"
timeout "$secs" esphome-dev logs "$(dirname "$0")/../esphome/sniffer.yaml" --device "$dev" 2>/dev/null \
  | grep --line-buffered -E '\[I\]\[F:' > "$out" || true
wc -l "$out"
