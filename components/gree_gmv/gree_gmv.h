#pragma once

#include "esphome/core/component.h"
#include "esphome/components/canbus/canbus.h"

#include <vector>

namespace esphome::gree_gmv {

// 29-bit identifier layout (see docs/04-protocol.md):
//   bits 28..16  prefix: 0x1EFF = status broadcast, 0x1CFF = poll, 0x1CBF = write command
//   bits 15..7   node address (0xD000 + 0x80*n for indoor units, 0xC400 outdoor)
//   bits 6..0    message type
static const uint32_t PREFIX_MASK = 0xFFFF0000;
static const uint32_t PREFIX_STATUS = 0x1EFF0000;
static const uint32_t PREFIX_WRITE = 0x1CBF0000;
static const uint16_t NODE_MASK = 0xFF80;
static const uint8_t TYPE_MASK = 0x7F;

enum MessageType : uint8_t {
  TYPE_SENSORS = 0x20,   // [0] room temp (°C = v-100), [1],[3] coil temps
  TYPE_STATE = 0x21,     // reported state: [0] mode, [1] fan+1, [2] swing
  TYPE_POWER = 0x6F,     // [0] bit0 = on
  TYPE_SETTINGS = 0x71,  // [0] mode, [1] fan, [2] swing vertical, [3] swing horizontal
  TYPE_SETPOINT = 0x73,  // LE16 0.1°C: [0..1] setpoint, [2..3] min, [4..5] max
};

enum GreeMode : uint8_t { MODE_COOL = 1, MODE_DRY = 2, MODE_FAN = 3, MODE_HEAT = 4 };
enum GreeFan : uint8_t { FAN_AUTO = 1, FAN_VERY_LOW = 2, FAN_LOW = 3, FAN_MEDIUM = 4, FAN_HIGH = 5, FAN_VERY_HIGH = 6 };
enum GreeSwing : uint8_t { SWING_OFF = 1, SWING_ON = 2 };

/// One chunk of a register: bytes [base, base+data.size()) of the node's register space for `type`.
/// Units send long registers as 7-byte chunks (byte 0 of the frame = offset). After a write they
/// immediately re-send only the first chunk, so chunks are delivered as they arrive, never reassembled.
struct Message {
  uint8_t type;
  uint8_t base;
  const std::vector<uint8_t> &data;
  /// Byte at absolute offset `off`, if covered by this message.
  bool get(uint8_t off, uint8_t &out) const {
    if (off < base || off - base >= data.size()) return false;
    out = data[off - base];
    return true;
  }
  bool get_u16(uint8_t off, uint16_t &out) const {
    uint8_t lo, hi;
    if (!get(off, lo) || !get(off + 1, hi)) return false;
    out = lo | (hi << 8);
    return true;
  }
};

class GreeGMVUnit {
 public:
  virtual uint16_t get_address() const = 0;
  virtual void on_message(const Message &msg) = 0;
};

class GreeGMV : public Component {
 public:
  void set_canbus(canbus::Canbus *bus) { this->canbus_ = bus; }
  void register_unit(GreeGMVUnit *unit) { this->units_.push_back(unit); }

  void setup() override;
  void dump_config() override;
  float get_setup_priority() const override { return setup_priority::DATA; }

  /// Write `len` bytes at `offset` of register `type` on node `address`.
  bool write(uint16_t address, uint8_t type, uint8_t offset, const uint8_t *value, size_t len);

 protected:
  void on_frame_(uint32_t can_id, bool extended, bool rtr, const std::vector<uint8_t> &data);

  canbus::Canbus *canbus_{nullptr};
  std::vector<GreeGMVUnit *> units_;
};

}  // namespace esphome::gree_gmv
