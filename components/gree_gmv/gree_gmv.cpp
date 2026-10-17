#include "gree_gmv.h"
#include "esphome/core/log.h"

namespace esphome::gree_gmv {

static const char *const TAG = "gree_gmv";

void GreeGMV::setup() {
  this->canbus_->add_callback([this](uint32_t can_id, bool extended, bool rtr, const std::vector<uint8_t> &data) {
    this->on_frame_(can_id, extended, rtr, data);
  });
}

void GreeGMV::dump_config() {
  ESP_LOGCONFIG(TAG, "Gree GMV hub: %u unit(s)", (unsigned) this->units_.size());
  for (auto *u : this->units_) ESP_LOGCONFIG(TAG, "  node 0x%04X", u->get_address());
}

void GreeGMV::on_frame_(uint32_t can_id, bool extended, bool rtr, const std::vector<uint8_t> &data) {
  if (!extended || rtr || data.empty()) return;
  if ((can_id & PREFIX_MASK) == PREFIX_WRITE && data.size() >= 3) {
    // Another controller (e.g. the vendor gateway) wrote a register: useful when debugging.
    ESP_LOGD(TAG, "observed write to 0x%04X type 0x%02X off=%u val=%02X", (unsigned) (can_id & NODE_MASK),
             (unsigned) (can_id & TYPE_MASK), data[0], data[2]);
    return;
  }
  if ((can_id & PREFIX_MASK) != PREFIX_STATUS) return;

  // Transport: byte 0 = offset of this chunk within the register, bytes 1..7 = payload.
  if (data.size() < 2) return;
  std::vector<uint8_t> chunk(data.begin() + 1, data.end());
  uint16_t node = can_id & NODE_MASK;
  Message msg{static_cast<uint8_t>(can_id & TYPE_MASK), data[0], chunk};
  for (auto *u : this->units_) {
    if (u->get_address() == node) u->on_message(msg);
  }
}

bool GreeGMV::write(uint16_t address, uint8_t type, uint8_t offset, const uint8_t *value, size_t len) {
  if (len == 0 || len > 6) return false;
  std::vector<uint8_t> frame;
  frame.reserve(2 + len);
  frame.push_back(offset);
  frame.push_back(static_cast<uint8_t>((1u << len) - 1));  // bitmask of bytes present
  frame.insert(frame.end(), value, value + len);
  uint32_t id = PREFIX_WRITE | address | (type & TYPE_MASK);
  auto err = this->canbus_->send_data(id, true, false, frame);
  if (err != canbus::ERROR_OK) {
    ESP_LOGW(TAG, "write to 0x%04X type 0x%02X failed (%d)", address, type, (int) err);
    return false;
  }
  ESP_LOGD(TAG, "write 0x%08X off=%u len=%u val=%02X", id, offset, (unsigned) len, value[0]);
  return true;
}

}  // namespace esphome::gree_gmv
