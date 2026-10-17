# gree-gmv-esp32

Control a Gree GMV5 VRF system (1 outdoor unit, 5 indoor units) from Home Assistant
with an ESP32 running ESPHome, talking directly to the VRF communication bus.

Status: **reading works end to end** (5 climate entities populated live from the bus via the
ESPHome component). **Writing is blocked on hardware**: the SN65HVD230 (3.3 V) cannot drive this
bus; a TJA1051T/3 board is on order. Read `docs/HANDOFF.md`.

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
    tx_pin: GPIO26
    rx_pin: GPIO27
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

Finding your unit addresses: flash `esphome/sniffer.yaml`, run `tools/capture.sh idle 60`, then
`tools/analyze.py captures/idle.log`; nodes appear as `1EFFxxxx` IDs, the node is bits 15..7.

## Layout

```
components/gree_gmv/   ESPHome external component (hub + climate platform)
esphome/               device configs: vrf.yaml (the real one), sniffer.yaml, diagnostics
docs/                  research, protocol findings, wiring, handoff
tools/                 capture / reassemble / diff scripts, API helpers
captures/              raw bus logs from the experiments
```

## Toolchain note

20 kbps on a classic ESP32 needs ESPHome newer than 2026.9 (the `esp32_can` component only
gained `20KBPS` for plain ESP32 on the dev branch). Until that ships in a release:

```
pipx install --suffix=-dev "git+https://github.com/esphome/esphome.git@dev"
cd esphome && esphome-dev run sniffer.yaml
```
