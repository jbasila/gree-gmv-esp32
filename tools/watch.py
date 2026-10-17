#!/usr/bin/env python3
"""Print reassembled messages only when their content changes vs. the last one on that ID.

usage: tools/watch.py captures/x.log          # replay a file
       tools/watch.py --after HH:MM:SS file   # only print changes after a time
Shows per-byte diff so that a setpoint or mode change stands out.
"""
import sys, argparse
sys.path.insert(0, __import__('os').path.dirname(__file__))
from reassemble import messages, node_type

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('log'); ap.add_argument('--after', default='00:00:00')
    ap.add_argument('--no-polls', action='store_true', help='hide 0x1CFF poll frames')
    ap.add_argument('--ids', help='comma list of hex IDs to show only')
    a = ap.parse_args()
    only = {int(x, 16) for x in a.ids.split(',')} if a.ids else None
    last = {}
    for ts, cid, base, msg in messages(a.log):
        if a.no_polls and cid >> 24 == 0x1C: continue
        if only and cid not in only: continue
        key = (cid, base)
        prev = last.get(key)
        last[key] = msg
        if prev == msg or ts < a.after: continue
        node, typ = node_type(cid)
        if prev is None:
            print(f"{ts} {cid:08X} node={node:03X} type={typ:02X} base={base:02X} NEW  {msg.hex(' ').upper()}")
            continue
        diff = []
        for i in range(max(len(prev), len(msg))):
            p = prev[i] if i < len(prev) else None
            n = msg[i] if i < len(msg) else None
            if p != n:
                diff.append(f"[{i}] {p if p is None else f'{p:02X}'}->{n if n is None else f'{n:02X}'}")
        print(f"{ts} {cid:08X} node={node:03X} type={typ:02X} base={base:02X} CHG  {msg.hex(' ').upper()}   {' '.join(diff)}")

if __name__ == '__main__':
    main()
