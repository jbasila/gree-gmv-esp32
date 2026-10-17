#!/usr/bin/env python3
"""Reassemble segmented Gree CAN messages from sniffer log lines.

A frame's byte 0 is the byte offset of its chunk inside a larger message, bytes 1..7 are
payload. A frame shorter than 8 bytes terminates the message.
"""
import re, collections

LINE = re.compile(r'\[(\d\d:\d\d:\d\d\.\d+)\]\[I\]\[F:\d+\]: ([XS]) ([0-9A-F]+) (\d) ?(.*)$')

def parse_line(ln):
    m = LINE.search(ln)
    if not m: return None
    ts, kind, cid, rtr, data = m.groups()
    return ts, kind, int(cid, 16), int(rtr), bytes.fromhex(data.replace(' ', ''))

def node_type(cid):
    low = cid & 0xFFFF
    return low & ~0x7F, low & 0x7F

class Reassembler:
    def __init__(self):
        self.cur = {}
    def feed(self, frame):
        """Returns (ts, cid, base_offset, message_bytes) when a message completes, else None."""
        ts, kind, cid, rtr, data = frame
        if kind != 'X' or len(data) < 1: return None
        if cid >> 24 == 0x1C:                        # poll frames: not segmented
            return (ts, cid, data[0], bytes(data[1:]))
        off, chunk = data[0], data[1:]
        st = self.cur.get(cid)
        if st is None or off - st[1] != len(st[2]):
            st = self.cur[cid] = (ts, off, bytearray())
        st[2].extend(chunk)
        if len(data) < 8:
            del self.cur[cid]
            return (st[0], cid, st[1], bytes(st[2]))
        return None

def messages(path):
    r = Reassembler()
    for ln in open(path, errors='replace'):
        f = parse_line(ln)
        if f is None: continue
        m = r.feed(f)
        if m: yield m
