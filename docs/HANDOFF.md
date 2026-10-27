# Handoff (updated 2026-10-27, session closed)

## Where we are

**The final board reads and writes on the real bus.** ESP32-C3 SuperMini (V1601, pads labelled by
GPIO) + TJA1051T/3 "CAN Pal" clone (AliExpress; chip marked NXP A1051/3), CANH/CANL at the
CoolAutomation gateway's bus terminals, **no GND wire**. Runs `esphome/vrf.yaml` (flashed over USB
2026-10-27; the HA ESPHome add-on's copy is the same C3 config). Five climate entities (Living Room
0xD000, Bedroom 1 0xD080, Bedroom 2 0xD100, Bedroom 3 0xD180, Bedroom 4 0xD200). Not yet in an enclosure.

Verified 2026-10-27 on Bedroom 3 from HA, each echoed by the unit, 0 bus errors / bus-off:

| control | frame | echo |
|---|---|---|
| setpoint 23 °C | (write not captured; unit broadcast `target=23.0`) | — |
| setpoint 24 °C | `write 0x1CBFD1F3 off=0 len=2 val=F0` | 308 ms |

GND → CANL at the C3 reads 1.3–2.0 V on a multimeter (jumps with traffic: CANL recessive ~2.5 V,
dominant ~1.5 V). Well inside the TJA's ±12 V common-mode range, so the floating ground is fine.

The earlier POC (ESP32 WROOM-32D, TX GPIO26 / RX GPIO27, GND tied to the gateway) proved setpoint, power,
fan, swing V and mode writes on 2026-10-26 (echoes 137–793 ms). It is dismantled; its boards are in boxes.

### CAN Pal clone wiring (C3 SuperMini)

| CAN Pal | C3 pad (left edge, top to bottom after 5V) |
|---|---|
| GND | **G** |
| Vcc | **3.3** (on-board charge pump makes the 5 V) |
| TX | **4** |
| RX | **3** |

SLNT left **unconnected** (the board keeps it in normal mode; it was never wired on the POC either).
Termination switch **OFF**. No VIO pin on this board: Vcc is the logic supply. Avoid pads 2/8/9
(strapping) and 20/21 (serial). Bench (`c3-tx-loop-test.yaml`, 100 Ω) 10/10, idle 0/50.

### Notes

- SuperMini WiFi: chip antenna sits next to the crystal; needs `output_power: 8.5dB` (in `vrf.yaml`).
- First USB connect on macOS needs the "Allow accessory to connect?" prompt approved, or no
  `/dev/cu.usbmodem*` appears.
- Switching `vrf.yaml` from classic ESP32 to C3 needs `esphome clean vrf.yaml` once (stale Xtensa flags:
  `unrecognized command-line option '-mlongcalls'`).
- An OTA built for the wrong chip is rejected by the board (`esp_ota_end failed (err=0x1503)`); seen
  when HA's dashboard still had the classic config. Harmless, but keep the dashboard copy in sync.
- `vrf_api_key` rotated 2026-10-27 (local `secrets.yaml`, the add-on's secrets, and the HA integration).
- Both AliExpress "SN65HVD230" modules are fakes (5 V dies; receive only). Not used. The Waveshare
  SN65HVD230 board (ordered 2026-10-18) has not arrived; it is a spare. The XIAO ESP32-C3 order is now a spare too.
- Changes from the iocControl app / cloud appear on the bus as `observed write` (gateway's 1CBF frames);
  our own writes log as `write 0x1CBF...`. Use that to tell them apart.
- After reflashing over USB, HA may not reconnect on its own; ESPHome integration → vrf → Reload.
- Keep `components/esp32_can/`: stable 2026.10.0 lacks bus-off recovery on every chip (and 20 kbps on
  classic ESP32). Both are on dev, so drop it at 2026.11.0 stable.

## Next: the enclosure

1. Decision so far: **keep the gateway on the bus** (iocControl app, fallback; its changes show in HA
   as `observed write`). Option to ask the dealer about a CoolAutomation local-control licence.
2. If the gateway is ever removed: first measure CANH–CANL powered off with and without it. 60 Ω → 120 Ω
   means it held a terminator → set the CAN Pal termination switch ON. Removing it loses iocControl/cloud.
3. Design and 3D-print the enclosure for the C3 + CAN Pal (one 4-pin header row; keep the chip antenna
   end of the C3 clear of metal and the gateway housing). Decide how the C3 is powered in the box (USB-C).
4. Untested on the C3 so far: power, mode, fan, swing writes and the other four units (same code path).

## Git identity (private project)

This is a private project: every commit must be `jbasila <jbasila@gmail.com>`, **never**
`<work email>` (the global `~/.gitconfig` default). The repo-local config sets
`user.name`/`user.email` and a credential helper that pushes as the `jbasila` GitHub account
(`gh auth token --user jbasila`), not `<work account>`. History was rewritten on 2026-10-27 to fix this.
Check before committing: `git config user.email` must print `jbasila@gmail.com`.

## Code map

- `components/gree_gmv/`: hub (`gree_gmv.cpp`: frame → chunk dispatch, discovery log, `write()`),
  climate platform (`gree_gmv_climate.cpp`: register → entity state, `control()` → writes).
- `components/esp32_can/`: verbatim ESPHome 2026.9.1 driver + 20 kbps on classic ESP32 + bus-off
  recovery. Delete once the add-on runs ESPHome ≥ 2026.11 (or restrict import to `components: [gree_gmv]`).
- `esphome/vrf.yaml`: the device config (also what the dashboard holds). `sniffer.yaml`,
  `tx-loop-test.yaml`, `tx-hold-test.yaml`, `tx-hold-forever.yaml`, `vrf-node.yaml`: diagnostics.
- `tools/`: `capture.sh`/`serial_log.py` (log serial), `analyze.py`/`watch.py`/`reassemble.py`
  (offline capture analysis), `states.py`/`press.py` (native API helpers; need the API key from
  `esphome/secrets.yaml`, gitignored).
- `docs/04-protocol.md`: the protocol. `docs/03-gateway-findings.md`: what the CoolAutomation box leaks.

## Protocol in one paragraph

CAN 2.0B, 20 kbps, 29-bit IDs. `0x1EFF` + node + type = status broadcast, `0x1CBF` + node + type =
write, `0x1CFF` = polls. Node = bits 15..7 (IDU n at 0xD000 + 0x80·(n−1), ODU 0xC400), type = bits
6..0. Registers are sent as 7-byte chunks, frame byte 0 = offset. Writes: `[offset, bitmask of bytes,
values...]`; the unit echoes the first chunk of the register within ~0.5 s. Registers: 0x6F power
(bit0), 0x71 mode/fan/swingV/swingH (mode 1 cool 2 dry 3 fan 4 heat; fan 1 auto..6 very high;
swing 1 off 2 on), 0x73 setpoint/min/max LE16 0.1 °C, 0x20 room temp (byte0 − 100 °C), 0x10 identity
(byte 16 = unit index).

## Open questions

- 0x6F bits 4/5 (`0x20`/`0x30` on idle units); 0x20 bytes 2/4/6..9; ODU registers (0x400 family).
- Whether heat is only refused during cooling (expected) — test in winter.
- The gateway's `myid:72F`: no frame from the gateway other than `1CBF` writes was identified.
- Horizontal swing and the other four units: untested (same code path, expected to work).
