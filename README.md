# gree-gmv-esp32

Control a Gree GMV5 VRF system (1 outdoor unit, 5 indoor units) from Home Assistant
with an ESP32 running ESPHome, talking directly to the VRF communication bus.

Status: **phase 1 done, phase 2 blocked on hardware**: SN65HVD230 (3.3 V) proven unable to drive this bus; needs a 5 V-side transceiver (TJA1051T/3 or ISO1050). Read `docs/HANDOFF.md`.

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

## Layout

```
docs/      research notes, protocol findings, wiring
esphome/   ESPHome configs (sniffer first, component later)
tools/     decode / correlate scripts for captured logs
```

## Toolchain note

20 kbps on a classic ESP32 needs ESPHome newer than 2026.9 (the `esp32_can` component only
gained `20KBPS` for plain ESP32 on the dev branch). Until that ships in a release:

```
pipx install --suffix=-dev "git+https://github.com/esphome/esphome.git@dev"
cd esphome && esphome-dev run sniffer.yaml
```
