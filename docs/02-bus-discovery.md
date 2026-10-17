# 02 — Bus discovery procedure

## Step 0: squeeze the existing gateway (no hardware needed)

1. Get the gateway IP: it toggles on the LCD every minute, or look at the router's DHCP table.
2. From a laptop on the same LAN:
   ```
   nc <gateway-ip> 10102
   ls2
   line
   ```
   `ls2` should list units like `L6.001 ON 024C 022.7 Low Cool OK - 0` (one line per IDU).
   If that works, add the CoolMasterNet integration in Home Assistant (host = gateway IP,
   port 10102). You now have HA control today, and a scripted way to poke the system while
   sniffing in phase 1.
3. Photograph: gateway sticker (model, S/N), gateway terminal block, and the ODU/IDU terminal
   block it is wired to. Note the terminal labels (G1/G2, D1/D2, H1/H2).

## Step 1: confirm it is CAN with a multimeter (power off nothing)

With the system running, measure each bus wire to the ODU chassis/earth:

| Reading | Meaning |
|---|---|
| both wires ~2.5 V DC, small jitter | CAN (CAN_H / CAN_L idle recessive). Expected. |
| one wire ~0 V, other 12–30 V DC with ripple | power-carrier (H1/H2 style). Different plan. |
| both ~0 V, or ~5 V on one | RS-485-ish or dead line. |

Then measure resistance across the pair with the system **powered off**: ~60 Ω means two
120 Ω terminators, i.e. textbook CAN.

## Step 2: measure the bit rate

Cheapest reliable way: a USB logic analyser (any 24 MHz Saleae clone, ~$10) + PulseView.
Probe CAN_H to GND, set the CAN decoder, read the shortest pulse width. 1/width = bit rate.
Try the ESPHome sniffer below at that rate.

Without a logic analyser: flash `esphome/sniffer.yaml` in listen-only mode and iterate the
`bit_rate` through 20/25/50/100/125 kbps. The correct rate is the one where frames decode and
the TWAI error counters stay at zero. Listen-only never sends ACKs, so a wrong guess cannot
disturb the VRF.

## Hardware shopping list

- ESP32 dev board. Any classic ESP32-WROOM-32 or ESP32-S3; all have TWAI (CAN) built in.
  Classic ESP32 rev < 2 cannot do below 25 kbps; S3/C3/C6 can. Prefer S3 to be safe.
- CAN transceiver breakout, **3.3 V logic**: SN65HVD230 (common, cheap) or TJA1051T/3.
  Do NOT use a 5 V MCP2551/TJA1050 without level shifting.
- Do not add a 120 Ω terminator; the bus is already terminated by Gree.
- Optional: USB logic analyser for PulseView.

## Wiring

```
ESP32 GPIO (tx_pin)  ->  transceiver CTX / D
ESP32 GPIO (rx_pin)  ->  transceiver CRX / R
ESP32 3V3            ->  transceiver VCC
ESP32 GND            ->  transceiver GND
transceiver CANH     ->  G1 (or D1)   (CAN is non-polar per Gree: if nothing decodes, swap)
transceiver CANL     ->  G2 (or D2)
```
Tap the bus in parallel at the same terminals the gateway uses. Keep stubs short.

## Transmit failure diagnosis (2026-10-17)

Symptom: listen-only RX perfect; first transmit → 31 bus errors, error-passive, bus-off, recovery.
Driver reported the frame as sent; the bus never saw it.

Diagnostic firmware `esphome/tx-loop-test.yaml` (raw GPIO: pull CTX low 30 µs, sample CRX):

| Condition | RX low while idle | RX low while TX low |
|---|---|---|
| on the Gree bus | 0–26 / 50 (bus traffic) | 3–9 / 10 (= background only) |
| disconnected from bus | 0 / 50 | 10 / 10 |

→ SN65HVD230 and wiring OK; the Gree bus cannot be pulled dominant by a 3.3 V transceiver
without a shared ground (two signal wires only, ESP32 powered from a laptop). Rs pin = 70 mV (ok),
CTX continuity ok, VCC 3.31 V. DMM on the live bus: CANH ≈ 2.4 V, CANL 0.7–1.4 V relative to
ESP32 GND, i.e. not a 2.5 V-centred bus from our board's point of view.

### Follow-up (2026-10-17 morning)

- Shared ground (ESP32 GND → gateway 12 V negative) changed nothing: loop test still 3–9/10 on-bus.
- Polarity note: when the two bus wires are swapped the receiver goes fully deaf (idle 0/50). Correct
  polarity = whichever gives ~15–35/50 idle on `tx-loop-test.yaml`.
- `tx-hold-test.yaml`: CTX held low for 6 s. RX pin sampled during the hold: 41–100/200 low, i.e. only the
  normal Gree traffic; our dominant never registers, not even at our own receiver. DMM across the pair
  during the hold: ~0.3–0.5 V. A 3.3 V SN65HVD230 cannot move this bus.
- **Conclusion: need a stronger transceiver.** Candidates:
  - TJA1051T/3 (5 V bus side, 3.3 V logic): direct drop-in, same 4 wires + 5 V from the ESP32's VIN/5V pin.
  - ISO1050 breakout (isolated, 5 V bus side, 3.3 V logic): also fixes any common-mode weirdness.
  - TJA1050 / MCP2551 modules are 5 V logic; ESP32's 3.3 V TX is below their 0.7·VCC VIH spec. Avoid.
