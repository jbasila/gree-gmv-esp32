# Handoff (updated 2026-10-17 22:30)

## Where we are

**Read side is in production.** The ESP32 (WROOM-32D rev 3.1 + SN65HVD230, CTX→GPIO26, CRX→GPIO27,
CANH/CANL tapped at the CoolAutomation gateway's bus terminals) runs `esphome/vrf.yaml`, managed by
the Home Assistant ESPHome add-on (stable 2026.9.1). Five climate entities (Living Room 0xD000,
Bedroom 1 0xD080, Bedroom 2 0xD100, Bedroom 3 0xD180, Bedroom 4 0xD200) show power, mode, fan, swing, setpoint
and room temperature; changes made in the iocControl app appear in HA within ~1 s.

**Write side is blocked on hardware: both "SN65HVD230" modules are fakes** (5 V dies at 3.3 V: receive
fine, cannot drive 100 Ω, and have a dominant timeout a real HVD230 lacks). Scope session 2026-10-17
evening (`docs/02-bus-discovery.md`): the Gree bus is ordinary CAN (idle ~2 V, dominant 3.8/0.4 V).
The earlier "3.3 V can't drive this bus" theory was wrong. A clone of the Adafruit 5708 CAN Pal
(TJA1051T/3) is ordered, ETA 2026-10-23..28; it is the right part. Until then a control from HA fails
harmlessly: the controller goes bus-off and recovers in ~300 ms, reads continue.

Repo is public: https://github.com/jbasila/gree-gmv-esp32. The dashboard config pulls the component
from `github://jbasila/gree-gmv-esp32@main` (refresh 10 min).

## Paused until new hardware arrives (TJA1051T/3 clone, ETA 2026-10-23..28)

Session ended 2026-10-17 22:30 with the read side back in production (`vrf.yaml` flashed over USB).
The fake HVD230 module is wired to the bus and the ESP32 GND is tied to the gateway GND.

### Arrival checklist, in order

1. **Fix the wiring before anything else.** The breadboard produced loose wires three times tonight and
   two false verdicts. Solder, or use a screw-terminal block, for VCC/GND/CTX/CRX and the bus pair.
2. Check the new board's power: the Adafruit 5708 original makes 5 V on-board from 3.3 V; a clone may
   need 5 V from the ESP32 VIN pin instead. Read the listing / look for a boost chip. The T/3 variant's
   logic pins are 3.3 V-compatible either way.
3. Cut its "Termination" solder jumper if it ships closed (the Gree bus is already terminated).
4. **Bench acceptance test, off the bus:** 100 Ω across CANH–CANL,
   `cd esphome && esphome-dev run tx-loop-test.yaml --device /dev/cu.usbserial-0001`
   → must read `rx low while tx driven low: 10/10`. The fakes read 0/10 here. Do NOT use
   `tx-hold-forever.yaml` for this: the TJA1051 has a dominant timeout and will always read "no drive".
5. Wire to the bus (TX→P26, RX→P27, CANH/CANL to the pair; if the receiver is deaf, swap the pair).
   Same loop test on the bus → 10/10, idle ~15–35/50.
6. `esphome run vrf.yaml --device /dev/cu.usbserial-0001` (or Install → Wirelessly from the HA dashboard).
7. In HA set Bedroom 3 to 24 °C. Serial log should show `write 0x1CBFD1F3 ...`, the unit's echo within
   ~0.5 s and no `bus-off`; the entity moves to 24.0. Then test mode, fan, swing, power.
8. If a write is accepted but a *mode* is refused (e.g. heat while the ODU cools), that is the VRF, not
   us: the entity simply stays as it was.

### Optional shortcut with the hardware already here

The fake modules are 5 V dies. Powered from the ESP32's VIN (5 V) their driver may work. Requirements:
a 2:1 resistor divider on CRX (5 V → 3.3 V; the ESP32 is not 5 V tolerant), and the same bench test
(step 4) before the bus. If the chip does not accept the ESP32's 3.3 V as "high" on CTX it simply never
transmits; harmless. Needs a resistor pair ~1:2 (e.g. 1 kΩ + 2.2 kΩ).

### Shopping list

| item | why | where |
|---|---|---|
| **Genuine 3.3 V-logic CAN transceiver** (one of): Waveshare SN65HVD230 CAN board (recommended: genuine TI, 3.3 V only) or Adafruit CAN Pal 5708 (TJA1051T/3, on-board 5 V boost) | the two AliExpress "SN65HVD230" modules are fakes; the TJA clone on order is also a clone | Waveshare's own store, Adafruit, Mouser, DigiKey, local shop |
| Solderable proto board + 2-pin screw terminal (or screw-terminal block + crimped Dupont leads) | the breadboard produced three loose wires and two wrong diagnoses in one evening | any |
| 1 kΩ + 2.2 kΩ resistors | only for the optional 5 V shortcut above (CRX divider) | any |

Already on hand and sufficient: ESP32 WROOM-32D, FNIRSI 1013D scope, multimeter, 100 Ω test resistor.
Not needed: another ESP32, terminators, logic analyser.

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
- After the TJA1051T/3 works: does our write need any sequencing (none observed from the gateway).
