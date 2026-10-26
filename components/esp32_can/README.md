# esp32_can override (temporary)

Verbatim copy of ESPHome 2026.9.1's `esp32_can` with two additions: `20KBPS` allowed on classic
ESP32 (silicon rev >= 2.0, set `esp32.framework.advanced.minimum_chip_revision: "3.0"` or your
revision), and bus-off recovery so a failed transmit does not stop receive until reboot.
Stable ESPHome 2026.10.0 has neither; the dev branch (2026.11) has both. Delete this folder once
you run 2026.11 stable, or restrict `external_components` to `components: [gree_gmv]`.
