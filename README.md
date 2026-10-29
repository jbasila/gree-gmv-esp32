# gree-gmv-esp32

Control a Gree GMV5 VRF system (1 outdoor unit, 5 indoor units) from Home Assistant
with an ESP32 running ESPHome, talking directly to the VRF communication bus.

Status: **reading and writing work end to end** (5 climate entities in Home Assistant; setpoint,
power, mode, fan and swing verified on the bus 2026-10-26). Use a genuine 3.3 V-logic transceiver
such as the TJA1051T/3 (Adafruit CAN Pal 5708 or a clone): the cheap "SN65HVD230" modules sold on
AliExpress are often 5 V fakes that receive but cannot transmit.

**Building one? Start with the step-by-step [build guide](docs/TUTORIAL.md)**: parts, wiring,
flashing, Home Assistant setup, a printable enclosure and troubleshooting.

## Plan

| Phase | Goal | Done when |
|---|---|---|
| 0 | Identify the bus (CAN vs. power-carrier vs. RS-485) and its bit rate | A logic-analyser / ESP32 capture decodes clean frames |
| 1 | Passive sniff, correlate frames with actions taken in iocControl / wired controller | Frame IDs + payload fields for power, mode, setpoint, fan, room temp are mapped |
| 2 | Inject commands from ESP32 (listen-only off) | ESP32 can turn one indoor unit on/off and set temperature |
| 3 | ESPHome external component exposing `climate` entities per indoor unit | 5 climate entities in Home Assistant |
| 4 | Publish | README + wiring + protocol doc good enough for a stranger |

See `docs/01-research.md` for what is already known and `docs/02-bus-discovery.md`
for the hands-on procedure.

## Usage

```yaml
external_components:
  - source: github://jbasila/gree-gmv-esp32   # or type: local, path: ../components

canbus:
  - platform: esp32_can
    id: vrf_can
    tx_pin: GPIO4         # ESP32-C3 SuperMini; avoid strapping pins 2/8/9 and serial 20/21
    rx_pin: GPIO3
    can_id: 0
    bit_rate: 20KBPS

gree_gmv:
  canbus_id: vrf_can

climate:
  - platform: gree_gmv
    name: "Living Room"
    address: 0xD000      # indoor unit n is at 0xD000 + 0x80 * (n-1)
```

Each `climate` entity gives power, mode (cool/heat/dry/fan), fan speed (auto, very low, low,
medium, high, very high), swing (vertical/horizontal), setpoint and room temperature.
See `esphome/vrf.yaml` for a complete config and `docs/04-protocol.md` for the protocol.

### Finding your unit addresses

Flash the config with the `gree_gmv:` hub and no `climate:` entries (or with guesses), open the
device log, and within a minute you get one line per unit on the bus:

```
[I][gree_gmv]: discovered indoor unit at address 0xD000 (not configured)
[I][gree_gmv]: indoor unit #1 is at address 0xD000
[I][gree_gmv]: discovered outdoor unit at address 0xC400
```

Copy the addresses into `climate:` entries, name them after the rooms, re-install. Which address is
which room: turn one unit on from its remote and watch which entity reacts.

## Layout

```
components/gree_gmv/   ESPHome external component (hub + climate platform)
esphome/               device configs: vrf.yaml (the real one), sniffer.yaml, diagnostics
docs/                  research, protocol findings, wiring, handoff
tools/                 capture / reassemble / diff scripts, API helpers
captures/              raw bus logs from the experiments
```

## Toolchain note

Stable ESPHome 2026.9 refuses `20KBPS` on a classic ESP32 (the chip does it from silicon rev 2).
This repo bundles a patched copy of the `esp32_can` driver under `components/esp32_can/` so the
stock ESPHome add-on builds it; it is a verbatim copy of 2026.9.1 plus the 20 kbps case and bus-off
recovery. Stable 2026.10.0 still lacks both; the dev branch (2026.11) has both, so from 2026.11 you
may restrict the import to `components: [gree_gmv]`. Verified to build on 2026.9.1, 2026.10.0 and dev.

## License

MIT, see `LICENSE`.
