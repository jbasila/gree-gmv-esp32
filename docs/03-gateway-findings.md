# 03 — What the CoolAutomation gateway told us (2026-10-16)

Talking to the gateway on TCP 10102 (CoolMaster ASCII API). Serial/MAC redacted.

```
> set
version       : 0.3.7D
build date    : Dec 12 2021
application   : Standard (Cloud Only)
HVAC lines    : 2
max indoors   : 8
aserver port  : 10102

> line
L2: TO Master U00/G00 myid:E5
L6: GMV5 Speed:20000 U00/G05 myid:72F Addr:N
    Tx:146/146 Rx:43923/45613 TO:0/0 CS:0/0 Col:7/7 NAK:0/0
```

## What that means

| Field | Reading |
|---|---|
| `GMV5` | line type: Gree GMV5 CAN |
| `Speed:20000` | **CAN bit rate 20 kbps**. Matches Gree's own GMV5 brochure ("bus speed up to 20 kBit/s"). |
| `G05` | 5 indoor units seen (our 5 rooms) |
| `myid:72F` | the gateway's own CAN identifier is 0x72F (fits 11-bit). Treat 0x72F as "the controller" when decoding. |
| `Rx:43923 / Tx:146` | bus is chatty: mostly status broadcasts, few commands. Sniffing will be productive. |
| `Addr:N` | gateway does not take a Gree address itself |

## Cloud Only lock

`ls2`, `stat*`, `query`, `on/off/temp`, `istat`, `ostat`, `pro`, `group`, `va` all return
`Command is not allowed in Cloud Only mode`. Only `set`, `line`, `ifconfig`, `help`, `props`
(empty table) work. So the Home Assistant CoolMasterNet integration will **not** work against
this box as licensed. Options:

1. Pay CoolAutomation for a "Standard" licence to unlock local API. Zero-engineering path.
2. Build the ESP32 CAN node (this repo). The gateway stays on the bus as a second controller
   and as a reference while reverse engineering via the iocControl app.

We are doing 2.

## Consequences for the hardware

- Bit rate 20 kbps: classic ESP32 silicon rev < 2 cannot do it. Our board is an ESP32-WROOM-32D with ESP32-D0WD-V3 rev 3.1: fine. ESPHome needs `esp32.framework.advanced.minimum_chip_revision: "2.0"` or higher for 20KBPS on classic ESP32.
  ESP32-S3 / C3 / C6, or a classic ESP32 with rev ≥ 2 (ESPHome's esp32_can supports 20KBPS there).
- The gateway's "Col:7" counter shows arbitration collisions happen on this bus; our node must
  use proper CAN arbitration (TWAI does), not bit-banging.
