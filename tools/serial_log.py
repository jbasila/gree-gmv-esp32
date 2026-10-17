#!/usr/bin/env python3
"""Raw serial logger with host timestamps, same line format esphome logs produces.
usage: serial_log.py <device> <outfile> [seconds]
"""
import sys, time, serial
dev, out = sys.argv[1], sys.argv[2]
secs = float(sys.argv[3]) if len(sys.argv) > 3 else 1e9
end = time.time() + secs
with serial.Serial(dev, 115200, timeout=1) as s, open(out, 'a', buffering=1) as f:
    while time.time() < end:
        ln = s.readline()
        if not ln: continue
        ts = time.strftime('%H:%M:%S') + f".{int((time.time() % 1) * 1000):03d}"
        f.write(f"[{ts}]{ln.decode(errors='replace').rstrip()}\n")
