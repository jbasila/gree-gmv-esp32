# Handoff — end of session 1 (2026-10-17, 00:30)

## Where we are

- **Bus fully identified**: Gree GMV5 CAN, 20 kbps, 29-bit IDs. Read side 100 % working with an
  ESP32-WROOM-32D (rev 3.1) + SN65HVD230 (WCMCU-230, 120 Ω terminator removed) in ESPHome listen-only.
- **Protocol decoded** far enough to build a climate component: node addresses for all 5 rooms, room
  temperature, setpoint/min/max, mode, fan speed, swing, power, and the exact write frames the
  CoolAutomation gateway uses. See `docs/04-protocol.md`.
- **Transmit blocked by electrical issue**: our 3.3 V transceiver cannot pull the Gree bus dominant.
  Proven with `esphome/tx-loop-test.yaml` (works off-bus, fails on-bus). Details and numbers in
  `docs/02-bus-discovery.md` → "Transmit failure diagnosis".
- The CoolAutomation gateway (192.168.1.32, TCP 10102) is "Cloud Only" licensed: local API refuses
  all control commands. `line` / `set` / `ifconfig` still work and were how we learned the bit rate.

## State of the hardware right now

- ESP32 is flashed with **`esphome/sniffer.yaml` (listen-only)**, safe to leave connected.
- **CANH / CANL are disconnected** from the gateway terminals (removed for the off-bus test).
- Wiring: CTX → P26 (GPIO26), CRX → P27 (GPIO27), 3V3, GND. No ground wire to the Gree side yet.

## Next steps, in order

1. ~~Ground test~~ done 2026-10-17: no effect. Polarity matters (see docs/02). Skip to step 2.
   negative (barrel jack outer contact or "-"/GND terminal). Reconnect CANH/CANL. Run the Mac on
   battery. Flash `esphome-dev run esphome/tx-loop-test.yaml` and expect `rx low while tx driven
   low: 10/10`. If yes → flash `esphome/vrf-node.yaml`, press "Bedroom 2 power ON" with
   `~/.local/pipx/venvs/esphome-dev/bin/python tools/press.py vrf-node.local "Bedroom 2 power ON"`
   and watch for `1EFFD16F ... 21 00 00 00` in the serial log (`tools/serial_log.py`).
2. **Ordered 2026-10-17**: AliExpress clone of Adafruit 5708 CAN Pal (TJA1051T/3), ETA Oct 23–28.
   On arrival: cut the "Termination" solder jumper (ships closed). Wire VCC→3V3, GND, TX→P26, RX→P27,
   CANH/CANL same polarity as before (if loop test idle reads 0/50, swap). SLNT unconnected.
   Run `tx-loop-test.yaml` → expect 10/10 on-bus, then `vrf-node.yaml` + `tools/press.py`.
   Original plan was: 5 V transceiver. Best fit is **TJA1051T/3** (5 V supply, 3.3 V
   logic, no level shifting). Alternatives: TJA1050/MCP2551 with a resistor divider on RX.
   Optional diagnostic before buying: hold CTX low for 1 s on the bus and DMM CANH/CANL; if the
   differential stays under 0.9 V the bus is simply too stiff for the 230.
3. **Once a write works**: build the ESPHome external component (`climate` per node), phase 3 in
   `README.md`. All decoding logic exists in Python in `tools/reassemble.py` and the field map.

## Tooling notes

- ESPHome **dev branch is required** (20 kbps on classic ESP32): installed as `esphome-dev` via pipx.
  Stable `esphome` 2026.9.1 refuses the bit rate.
- `esphome-dev logs` is fragile with a stale validated-config cache; `tools/serial_log.py` (pyserial,
  run with the esphome-dev venv python) is the reliable logger.
- Captures in `captures/`: `idle.log` (60 s baseline), `experiment1.log`/`experiment2.log` (all app
  actions with timestamps), `loop-test*.log`. `tools/watch.py <log> --no-polls` shows changes.
- Nothing is committed yet. `git add -A && git commit` when ready; `esphome/secrets.yaml` is ignored.

## Open questions for the protocol

- Meaning of 0x6F bits 4/5 (`0x20`/`0x30` on idle units), 0x20 bytes 2/4/6/7/8/9, ODU messages.
- Whether heat is refused only while the ODU is cooling (expected VRF behaviour) or needs another field.
- Which node, if any, carries the gateway's `myid:72F`; no frame from the gateway other than the
  `1CBF` writes was identified.
