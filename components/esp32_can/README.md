# esp32_can override (temporary)

Verbatim copy of ESPHome 2026.9.1's `esp32_can` with one addition: `20KBPS` allowed on classic
ESP32 (silicon rev >= 2.0, set `esp32.framework.advanced.minimum_chip_revision: "3.0"` or your
revision). ESPHome 2026.10 ships this upstream; delete this folder once you run that version,
or restrict `external_components` to `components: [gree_gmv]`.
