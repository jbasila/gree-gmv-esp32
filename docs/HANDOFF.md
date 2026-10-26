# Handoff (updated 2026-10-26)

## Where we are

**Read and write both work in production.** ESP32 (WROOM-32D) + TJA1051T/3 "CAN Pal" clone
(AliExpress; chip marked NXP A1051/3), CTX→GPIO26, CRX→GPIO27, CANH/CANL tapped at the CoolAutomation
gateway's bus terminals, ESP32 GND tied to the gateway GND. Runs `esphome/vrf.yaml` from the HA ESPHome
add-on (now 2026.10.0). Five climate entities (Living Room 0xD000, Bedroom 1 0xD080, Bedroom 2 0xD100,
Bedroom 3 0xD180, Bedroom 4 0xD200).

Verified 2026-10-26 on Bedroom 3 from HA, each echoed by the unit, no bus-off:

| control | frame | echo |
|---|---|---|
| setpoint 23 °C | `write 0x1CBFD1F3 off=0 len=2 val=E6` | 459 ms |
| power on | `write 0x1CBFD1EF off=0 len=1 val=01` | 312 ms |
| fan high | `write 0x1CBFD1F1 off=1 len=1 val=05` | 137 ms |
| swing V on | `write 0x1CBFD1F1 off=2 len=2 val=02` | 438 ms |
| mode fan | `write 0x1CBFD1F1 off=0 len=1 val=03` | 793 ms |

### CAN Pal clone wiring

Vcc → ESP32 **3V3** (on-board charge pump makes the 5 V), GND → GND, TX → GPIO26, RX → GPIO27,
**SLNT → GND** (high = listen-only). Termination switch **OFF**. There is no VIO pin on this board:
Vcc is the logic supply. Bench test (100 Ω, off bus) read 10/10; on the bus 10/10 with idle 16–30/50.

### Notes

- Both AliExpress "SN65HVD230" modules are fakes (5 V dies; receive only). Not used.
- The Waveshare SN65HVD230 board (ordered 2026-10-18) has not arrived; it is now a spare.
- Changes from the iocControl app / cloud appear on the bus as `observed write` (gateway's 1CBF frames);
  our own writes log as `write 0x1CBF...`. Use that to tell them apart.
- After reflashing over USB, HA did not reconnect on its own; ESPHome integration → vrf → Reload fixed it.
- The add-on is now ESPHome ≥ 2026.10: `components/esp32_can/` can probably be dropped (see Code map).

## Code map

- `components/gree_gmv/`: hub (`gree_gmv.cpp`: frame → chunk dispatch, discovery log, `write()`),
  climate platform (`gree_gmv_climate.cpp`: register → entity state, `control()` → writes).
- `components/esp32_can/`: verbatim ESPHome 2026.9.1 driver + 20 kbps on classic ESP32 + bus-off
  recovery. Delete once the add-on runs ESPHome ≥ 2026.10 (or restrict import to `components: [gree_gmv]`).
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
