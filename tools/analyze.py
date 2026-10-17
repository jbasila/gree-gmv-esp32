#!/usr/bin/env python3
"""Summarise a sniffer capture: per-ID counts, J1939-style ID split, payload variability.

usage: tools/analyze.py captures/idle.log [--diff captures/other.log]
Log lines look like: [23:14:59.606][I][F:012]: X 1CFFD26E 0 01 02
"""
import re, sys, collections, argparse

LINE = re.compile(r'\[(\d\d:\d\d:\d\d\.\d+)\]\[I\]\[F:\d+\]: ([XS]) ([0-9A-F]+) (\d) ?(.*)$')

def load(path):
    frames = []
    for ln in open(path, errors='replace'):
        m = LINE.search(ln)
        if not m: continue
        ts, kind, cid, rtr, data = m.groups()
        frames.append((ts, kind, int(cid, 16), int(rtr), bytes.fromhex(data.replace(' ', ''))))
    return frames

def split29(cid):
    prio = (cid >> 26) & 0x7
    pf = (cid >> 16) & 0xFF
    ps = (cid >> 8) & 0xFF
    sa = cid & 0xFF
    return prio, pf, ps, sa

def summarise(frames, label):
    by_id = collections.defaultdict(list)
    for ts, kind, cid, rtr, data in frames:
        by_id[(kind, cid)].append(data)
    print(f"== {label}: {len(frames)} frames, {len(by_id)} unique IDs")
    print(f"{'kind':4} {'id':>8} {'pri':>3} {'pf':>2} {'ps':>2} {'sa':>2} {'n':>5} {'lens':>8}  payloads(unique, first 4)")
    for (kind, cid), datas in sorted(by_id.items(), key=lambda kv: -len(kv[1])):
        uniq = list(dict.fromkeys(datas))
        lens = sorted({len(d) for d in datas})
        if kind == 'X':
            p, pf, ps, sa = split29(cid)
            idcol = f"{cid:08X} {p:3d} {pf:02X} {ps:02X} {sa:02X}"
        else:
            idcol = f"{cid:08X} {'':3} {'':2} {'':2} {'':2}"
        ex = ' | '.join(d.hex(' ').upper() for d in uniq[:4])
        print(f"{kind:4} {idcol} {len(datas):5d} {str(lens):>8}  [{len(uniq)} uniq] {ex}")
    return by_id

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('log'); ap.add_argument('--diff')
    a = ap.parse_args()
    base = summarise(load(a.log), a.log)
    if a.diff:
        other = summarise(load(a.diff), a.diff)
        print("\n== IDs only in", a.diff)
        for k in other:
            if k not in base:
                print(f"  {k[0]} {k[1]:08X}  n={len(other[k])}")
        print("== IDs with new payload values in", a.diff)
        for k in other:
            if k in base:
                new = set(other[k]) - set(base[k])
                if new:
                    print(f"  {k[0]} {k[1]:08X}: {len(new)} new payloads, e.g. {sorted(new)[0].hex(' ').upper()}")

if __name__ == '__main__':
    main()
