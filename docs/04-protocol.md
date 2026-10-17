# 04 — Protocol findings (living document)

Everything here is inferred from passive captures in `captures/`. Hypotheses are marked (?).

## Physical / link layer

- CAN 2.0B, **20 kbps**, 29-bit extended identifiers only (no 11-bit frames seen).
- Idle bus: ~130 frames/s, ~115 distinct IDs with 1 ODU + 5 IDUs + CoolAutomation gateway.

## Identifier layout

```
 28..26  25..24  23..16  15..7   6..0
 prio    (2b)    0xFF    node    type
```

Seen prefixes: `0x1EFF....` (prio 7, bits 25..24 = 10) carries status/data, `0x1CFF....` (bits 25..24 = 00) carries short polls.

The low 16 bits split into a **node address** (bits 15..7, i.e. multiples of 0x80) and a
**message type** (bits 6..0):

| Node | Who (?) | Evidence |
|---|---|---|
| 0xD000 | IDU 1 | type 0x10 msg ends with `01 00 20 00` |
| 0xD080 | IDU 2 | `... 02 00 02 00` |
| 0xD100 | IDU 3 | `... 03 00 22 00`; emits extra types 0x14, 0x22..0x27, 0x29 (has the wired controller? master IDU?) |
| 0xD180 | IDU 4 | `... 04 00 04 00` |
| 0xD200 | IDU 5 | `... 05 00 05 00` |
| 0xC400 | ODU | big type 0x10 (41 bytes), types 0x27/0x28/0x31/0x32 unique to it |
| ? | CoolAutomation gateway | reports `myid:72F`; no frames attributed yet (it transmits rarely) |

## Transport: segmented messages

Each frame's **byte 0 is the byte offset** of the chunk within a larger message; bytes 1..7 are
payload (7 bytes per full frame). A frame shorter than 8 bytes ends the message. Offsets seen
start at 0x00 (data messages) or 0x50 (ODU status messages, i.e. a different "page"/base) and
step by 7: `00, 07, 0E, 15 ...` / `50, 57, 5E, 65 ...`.

The `0x1CFF` poll frames break this pattern: byte 0 is `0x32`, `0x42` or `0x23` followed by `00`
and they repeat every ~625 ms per unit. Treat byte 0 as a request/ack code there (?).

## Per-IDU message types (reassembled, idle)

| Type | Len | Example (IDU 1) | Guess |
|---|---|---|---|
| 0x10 | 20 | `0A 00 0A 00 4C 60 20 CB 99 F7 1C 00 00 00 70 00 01 00 20 00` | identity: serial-ish bytes 4..10, unit index at byte 16, capacity/model at 18? |
| 0x11 | 3..10 | `0D 1B 01` | version? |
| 0x20 | 25 | `7B 7A 46 7B 46 7B 46 7F 64 91 00.. 64` | sensors: several ~0x7B values look like temperatures (encoding TBD), 0x64 = 100 % |
| 0x21 | 18 | `01 01 01 01 01 01 00 05 10 10 01 01 03 01 0A 01 07 00` | operating state: power/mode/fan/setpoint flags |
| 0x31 | 6 | `00 00 00 00 D2 04` | 0x04D2 = 1234 → counter/hours? |
| 0x32 | 2..4 | `1F 00` | |
| 0x6D..0x72 | 1..4 | polls `32 00`, `23 00`, `32 00 00 00 00` | request/ack, 1.6 Hz |
| 0x71 | 20 | `01 04 01 01 00 05 10 10 01 00 03 0A 01 01 00 00 00 00 00 07` | looks like 0x21's sibling: settings as received/echoed? |
| 0x73 | 6 | `FA 00 A0 00 2C 01` | 250, 160, 300 → limits (0.1 °C? 25.0/16.0/30.0!) |

0x73 = `FA 00 A0 00 2C 01` reads as little-endian 250 / 160 / 300 → 25.0 / 16.0 / 30.0 °C.
So temperatures elsewhere may also be LE16 in 0.1 °C or 8-bit in 0.5 °C steps (?).

## ODU (0x400) message types

| Type | Len | Example | Guess |
|---|---|---|---|
| 0x10 | 41 | `0A 00 0A 00 33 60 08 84 40 7E 1D ...` | identity |
| 0x20 | 6 (base 0xC8) | `64 64 6D 64 77 00` | fan/compressor % |
| 0x21 | 15 | `01 02 01 01 0D 03 01 00 01 00 00 00 00 00 01` | state |
| 0x27 | 25 | `00 00 20 03 29 20 03 30 20 03 25 20 05 27 20 04 04 02 ...` | `20 03` = 800 LE repeated → pressures/temps ×? |
| 0x28 | 15 | `01 05 00 01 FF 00 00 00 20 01 01 01 01 01 01` | 0x05 at byte 1 = number of IDUs? |
| 0x31 | 6 | `00 00 2D 06 40 06` | 0x062D=1581, 0x0640=1600 |
| 0x32 | 6 | `31 45 4C 50 31 45` | ASCII "1ELP1E" → model string fragments? |

## Other

- `0x04820084` (prio 1) every ~200 ms, 8 bytes `20 04 19 13 40 34 00 02` with byte 5 incrementing: a clock/heartbeat, source unknown.

## Next experiment

Toggle one IDU in iocControl while capturing; diff reassembled 0x21 / 0x71 / 0x20 messages.

## Write commands (confirmed 2026-10-16, experiment 1)

The CoolAutomation gateway writes with identifier prefix **`0x1CBF`** (vs `0x1CFF` for
polls/reads) + node + type. Data = `<offset> <?> <value bytes...>`:

```
1CBF D1EF  00 01 00        IDU4 type 6F off 0 := 00      power OFF
1CBF D1EF  00 01 01        IDU4 type 6F off 0 := 01      power ON
1CBF D1F1  00 01 03        IDU4 type 71 off 0 := 03      mode FAN
1CBF D1F1  00 01 01        IDU4 type 71 off 0 := 01      mode COOL
1CBF D1F1  01 01 06        IDU4 type 71 off 1 := 06      fan speed 6 (high)
1CBF D1F1  01 01 03        IDU4 type 71 off 1 := 03      fan speed 3
1CBF D1F3  00 03 04 01     IDU4 type 73 off 0 := 0x0104  setpoint 26.0 °C (LE16, 0.1 °C)
1CBF D1F3  00 03 FA 00     IDU4 type 73 off 0 := 250     setpoint 25.0 °C
1CBF D1F3  00 03 E6 00     IDU4 type 73 off 0 := 230     setpoint 23.0 °C
```

Second data byte is a **bitmask of the bytes that follow**: `01` = one byte, `03` = two bytes.
The target node re-broadcasts **only the first 8-byte chunk** of the affected register (`1EFF node type`,
offset 0, 7 payload bytes) within ~100–900 ms: that is the ack. The full multi-chunk dump of the
register only comes with the periodic cycle (every ~20 s), so consumers must act on chunks as they
arrive rather than reassembling (the ESPHome component does this). The 0x21 state message follows
~1–4 s later.

### Field map so far

| Type | Off | Field | Encoding |
|---|---|---|---|
| 0x6F | 0 | power | bit0 = on. Bits 4/5 seen set on idle units (`0x20`, `0x30`): unknown flags |
| 0x71 | 0 | mode | 1 = cool, 2 = dry, 3 = fan, 4 = heat (refused while ODU cools: state never changed). auto: app has none |
| 0x71 | 1 | fan speed | 1 auto, 2 very low, 3 low, 4 medium, 5 high, 6 very high (0x21 byte 1 reports value+1) |
| 0x71 | 2..3 | swing | two bytes (vertical, horizontal?), 1 = off, 2 = on; 0x21 byte 2 mirrors |
| 0x73 | 0..1 | setpoint | LE16, 0.1 °C |
| 0x73 | 2..3 | min setpoint | LE16, 0.1 °C (160 = 16.0) |
| 0x73 | 4..5 | max setpoint | LE16, 0.1 °C (300 = 30.0) |
| 0x21 | 0 | mode (status) | mirrors 0x71[0] |
| 0x21 | 1 | fan (status) | 0x71[1] + 1; `01` when off |
| 0x20 | 0 | room temp | °C = value − 100. Matched 4 of 5 idle units exactly; the running unit read 2 °C above the app (Gree cooling-mode ambient compensation, presumably). Byte 5 duplicates byte 0. |
| 0x20 | 1, 3 | coil temps | °C = value − 100 (running cooling unit: 1 °C and 7 °C; idle units ≈ room temp) |
| 0x20 | 2, 4, 6 | ? | 0x46 (= −30) on an idle unit → probably "n/a"; different encoding or absent sensor |
| 0x20 | 7, 8 | ? | 0x64 = 100 % / 0x7F / 0x7D |

### Room mapping

| Node | Room | Evidence |
|---|---|---|
| 0xD000 | Living room | setpoint write (exp 2) |
| 0xD080 | Bedroom 1 | power write (exp 2) |
| 0xD100 | Bedroom 2 | power write (exp 2); emits extra types 0x14, 0x22..0x27, 0x29 (wired controller here?) |
| 0xD180 | Bedroom 3 | all experiment-1 writes targeted it |
| 0xD200 | Bedroom 4 | by elimination |
