# 01 — Research (2026-10-16)

## The dealer gateway is a CoolAutomation device

- `iocControl` is CoolAutomation's app (Play Store id `com.coolautomation.ioccontrol`).
- Gree sells the gateway as **GMVCGA01**. Its install guide says:
  - VRF system type: "GREE – GMV5 (L6)", max 8 indoor units, 12 VDC, Ethernet RJ-45, LCD.
  - Wiring step 1: "Connect L6 (G1 G2) to the outdoor unit terminal or to indoor unit line".
  - LCD shows "HVAC lines (L1 and L2) communication status: RX, TX" and unit IDs like `L2.001`.
- `L6`, `L1.xxx` unit IDs and an LCD are CoolMaster / CoolMasterNet conventions. So this box
  almost certainly speaks the **CoolMaster ASCII API on TCP port 10102** (`ls2`, `on L2.001`,
  `temp L2.001 24`, ...), and Home Assistant already has a built-in **CoolMasterNet** integration
  (`pycoolmasternet_async`). That is the fast path to HA control and, more importantly for this
  project, a ground truth we can correlate bus captures against.

Sources:
- https://www.greecomfort.com/assets/our-products/multipro-controls/documents/cool-automation-multipro-controls-installation-manual-gmv-cga01.pdf
- https://play.google.com/store/apps/details?id=com.coolautomation.ioccontrol
- https://support.coolautomation.com/hc/en-us/articles/7068465434397-CoolMaster-PRM-Programmers-Reference-Manual
- https://www.home-assistant.io/integrations/coolmaster/

## What the two wires probably are

Gree GMV5 has three different 2-wire buses. Do not confuse them:

| Terminals | Where | What Gree says | Likely physical layer |
|---|---|---|---|
| D1 / D2 | ODU ↔ IDUs ("CAN1") | "new generation CAN communication network, auto addressing, non-polar" | CAN, terminated at ODU |
| G1 / G2 | ODU ↔ centralized controllers / other ODUs ("CAN2") | centralized controller port, matching resistor on last ODU | CAN |
| H1 / H2 | IDU ↔ wired controller (XK46/XK55...) | "dual wire power carrier: power and communication on one pair" | NOT plain CAN, power + modulated data |

The gateway guide says G1/G2 on the ODU *or* the indoor unit line (D1/D2). Both are CAN.
So the working hypothesis is **CAN bus, bit rate unknown**. Nobody has published the rate or
the frame format for Gree GMV CAN as of this search; it has to be measured.

Sources:
- https://www.manualslib.com/manual/4025010/Gree-Gmv5.html
- https://www.manualslib.com/manual/1590927/Gree-Gmv5-Series.html
- https://cdn.bakerdist.com/gree_gmv-96wmb-fu_article_1472200335416_en_cc1.pdf

## Prior art (none covers GMV CAN; useful for technique)

- https://github.com/maxim-smirnov/gree-wired-proto — XK19 wired controller on split units: RS-485, 1200 8N1, `7E 7E` header, XOR checksum. Different bus, but Gree likes XOR checksums and `7E` headers.
- https://github.com/bekmansurov/gree-hvac-protocol — Gree WiFi-module UART protocol.
- https://github.com/sgtaziz/esphome_gree_modbus — Gree commercial units via Modbus RTU (needs Gree COM-BMS board). Not our path.
- https://man.kievclimate.com/man/Gree/GMV/BMS/Modbus%20Protocol%20(V1.2)%202018.11.01.pdf — Gree GMV BMS Modbus register map. Useful later as a hint of which parameters exist per IDU.
- https://github.com/hencou/esphome_gvret — ESPHome GVRET: stream CAN frames to SavvyCAN over WiFi. Sniffing tool of choice once rate is known.
- https://esphome.io/components/canbus/esp32_can/ — ESP32 TWAI driver, has listen-only mode.

## Open questions

1. Exact CoolAutomation model behind GMVCGA01 (CoolMaster? CooLinkBridge?). Check sticker.
2. Which terminals the dealer actually wired: ODU G1/G2 or IDU D1/D2?
3. ~~CAN bit rate~~ 20 kbps, confirmed (docs/03).
4. 11-bit or 29-bit IDs, and whether IDs encode the unit address.
