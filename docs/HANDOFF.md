# Handoff (updated 2026-10-17 12:30)

## Where we are

**Read side is in production.** The ESP32 (WROOM-32D rev 3.1 + SN65HVD230, CTX→GPIO26, CRX→GPIO27,
CANH/CANL tapped at the CoolAutomation gateway's bus terminals) runs `esphome/vrf.yaml`, managed by
the Home Assistant ESPHome add-on (stable 2026.9.1). Five climate entities (Living Room 0xD000,
Bedroom 1 0xD080, Bedroom 2 0xD100, Bedroom 3 0xD180, Bedroom 4 0xD200) show power, mode, fan, swing, setpoint
and room temperature; changes made in the iocControl app appear in HA within ~1 s.

**Write side is blocked on hardware.** The SN65HVD230 (3.3 V) cannot pull the Gree bus dominant
(proven with `esphome/tx-loop-test.yaml` and `tx-hold-test.yaml`, see `docs/02-bus-discovery.md`).
A clone of the Adafruit 5708 CAN Pal (TJA1051T/3) is ordered, ETA 2026-10-23..28. Until then a
control from HA fails harmlessly: the controller goes bus-off and recovers in ~300 ms, reads continue.

Repo is public: https://github.com/jbasila/gree-gmv-esp32. The dashboard config pulls the component
from `github://jbasila/gree-gmv-esp32@main` (refresh 10 min).

## When the TJA1051T/3 arrives

1. Cut its "Termination" solder jumper (ships closed; the Gree bus is already terminated).
2. Wire: VCC→ESP32 3V3 (board makes its own 5 V), GND, TX→P26, RX→P27, CANH/CANL to the bus pair in
   the polarity that worked (if the receiver is deaf, swap). SLNT unconnected.
3. From a Mac checkout: `cd esphome && esphome-dev run tx-loop-test.yaml` → expect
   `rx low while tx driven low: 10/10` on the bus. (Needs `esphome-dev` = pipx dev install; the
   stable `esphome` also works for `vrf.yaml` thanks to the bundled driver override.)
4. Re-install `vrf` from the HA dashboard (Install → Wirelessly) or `esphome run vrf.yaml` over USB.
5. In HA set Bedroom 3 to 24 °C. Serial log should show `write 0x1CBFD1F3 ...` with no `bus-off`,
   and the entity should move to 24.0 within a second. Then test mode, fan, swing, power.
6. If a write is accepted but a *mode* is refused (e.g. heat while the ODU cools), that is the VRF,
   not us: the entity simply stays as it was.

## Code map

- `components/gree_gmv/`: hub (`gree_gmv.cpp`: frame → chunk dispatch, discovery log, `write()`),
  climate platform (`gree_gmv_climate.cpp`: register → entity state, `control()` → writes).
- `components/esp32_can/`: verbatim ESPHome 2026.9.1 driver + 20 kbps on classic ESP32 + bus-off
  recovery. Delete once the add-on runs ESPHome ≥ 2026.10 (or restrict import to `components: [gree_gmv]`).
- `esphome/vrf.yaml`: the device config (also what the dashboard holds). `sniffer.yaml`,
  `tx-loop-test.yaml`, `tx-hold-test.yaml`, `vrf-node.yaml`: diagnostics.
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
- After the TJA1051T/3 works: does our write need any sequencing (none observed from the gateway).
