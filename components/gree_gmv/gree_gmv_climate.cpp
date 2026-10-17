#include "gree_gmv_climate.h"
#include "esphome/core/log.h"

#include <cmath>
#include <cstring>

namespace esphome::gree_gmv {

static const char *const TAG = "gree_gmv.climate";
static const char *const FAN_NAME_VERY_LOW = "Very Low";
static const char *const FAN_NAME_VERY_HIGH = "Very High";

void GreeGMVClimate::setup() {
  // Custom fan modes live on the entity (traits-level setter is deprecated).
  this->set_supported_custom_fan_modes({FAN_NAME_VERY_LOW, FAN_NAME_VERY_HIGH});
}

void GreeGMVClimate::dump_config() {
  LOG_CLIMATE("", "Gree GMV indoor unit", this);
  ESP_LOGCONFIG(TAG, "  node address: 0x%04X", this->address_);
}

climate::ClimateTraits GreeGMVClimate::traits() {
  climate::ClimateTraits t;
  t.set_feature_flags(climate::CLIMATE_SUPPORTS_CURRENT_TEMPERATURE);
  t.set_supported_modes({climate::CLIMATE_MODE_OFF, climate::CLIMATE_MODE_COOL, climate::CLIMATE_MODE_HEAT,
                         climate::CLIMATE_MODE_DRY, climate::CLIMATE_MODE_FAN_ONLY});
  t.set_supported_fan_modes({climate::CLIMATE_FAN_AUTO, climate::CLIMATE_FAN_LOW, climate::CLIMATE_FAN_MEDIUM,
                             climate::CLIMATE_FAN_HIGH});
  t.set_supported_swing_modes({climate::CLIMATE_SWING_OFF, climate::CLIMATE_SWING_BOTH,
                               climate::CLIMATE_SWING_VERTICAL, climate::CLIMATE_SWING_HORIZONTAL});
  t.set_visual_min_temperature(this->min_temp_);
  t.set_visual_max_temperature(this->max_temp_);
  t.set_visual_target_temperature_step(1.0f);
  t.set_visual_current_temperature_step(1.0f);
  return t;
}

void GreeGMVClimate::on_message(const Message &msg) {
  uint8_t b;
  uint16_t w;
  bool changed = false;
  switch (msg.type) {
    case TYPE_SENSORS:
      if (msg.get(0, b)) {
        this->current_temperature = static_cast<float>(b) - 100.0f;
        changed = true;
      }
      break;
    case TYPE_POWER:
      if (msg.get(0, b)) {
        this->power_ = b & 0x01;
        changed = true;
      }
      break;
    case TYPE_SETTINGS:
      if (msg.get(0, b)) { this->gree_mode_ = b; changed = true; }
      if (msg.get(1, b)) { this->gree_fan_ = b; changed = true; }
      if (msg.get(2, b)) { this->swing_v_ = b; changed = true; }
      if (msg.get(3, b)) { this->swing_h_ = b; changed = true; }
      break;
    case TYPE_SETPOINT:
      if (msg.get_u16(0, w)) { this->target_temperature = w / 10.0f; changed = true; }
      if (msg.get_u16(2, w)) this->min_temp_ = w / 10.0f;
      if (msg.get_u16(4, w)) this->max_temp_ = w / 10.0f;
      break;
    default:
      break;
  }
  if (changed) this->publish_from_bus_();
}

void GreeGMVClimate::publish_from_bus_() {
  if (!this->power_) {
    this->mode = climate::CLIMATE_MODE_OFF;
  } else {
    switch (this->gree_mode_) {
      case MODE_COOL: this->mode = climate::CLIMATE_MODE_COOL; break;
      case MODE_DRY: this->mode = climate::CLIMATE_MODE_DRY; break;
      case MODE_FAN: this->mode = climate::CLIMATE_MODE_FAN_ONLY; break;
      case MODE_HEAT: this->mode = climate::CLIMATE_MODE_HEAT; break;
      default:
        ESP_LOGW(TAG, "0x%04X: unknown mode %u", this->address_, this->gree_mode_);
        break;
    }
  }
  switch (this->gree_fan_) {
    case FAN_AUTO: this->set_fan_mode_(climate::CLIMATE_FAN_AUTO); break;
    case FAN_VERY_LOW: this->set_custom_fan_mode_(FAN_NAME_VERY_LOW); break;
    case FAN_LOW: this->set_fan_mode_(climate::CLIMATE_FAN_LOW); break;
    case FAN_MEDIUM: this->set_fan_mode_(climate::CLIMATE_FAN_MEDIUM); break;
    case FAN_HIGH: this->set_fan_mode_(climate::CLIMATE_FAN_HIGH); break;
    case FAN_VERY_HIGH: this->set_custom_fan_mode_(FAN_NAME_VERY_HIGH); break;
    default:
      ESP_LOGW(TAG, "0x%04X: unknown fan speed %u", this->address_, this->gree_fan_);
      break;
  }
  bool v = this->swing_v_ == SWING_ON, h = this->swing_h_ == SWING_ON;
  this->swing_mode = v && h ? climate::CLIMATE_SWING_BOTH
                     : v    ? climate::CLIMATE_SWING_VERTICAL
                     : h    ? climate::CLIMATE_SWING_HORIZONTAL
                            : climate::CLIMATE_SWING_OFF;
  ESP_LOGD(TAG, "'%s' power=%d mode=%u fan=%u swing=%u/%u target=%.1f current=%.1f", this->get_name().c_str(),
           this->power_, this->gree_mode_, this->gree_fan_, this->swing_v_, this->swing_h_, this->target_temperature,
           this->current_temperature);
  this->publish_state();
}

void GreeGMVClimate::control(const climate::ClimateCall &call) {
  if (call.get_mode().has_value()) {
    auto m = *call.get_mode();
    if (m == climate::CLIMATE_MODE_OFF) {
      uint8_t off = 0;
      this->parent_->write(this->address_, TYPE_POWER, 0, &off, 1);
    } else {
      uint8_t gm = 0;
      switch (m) {
        case climate::CLIMATE_MODE_COOL: gm = MODE_COOL; break;
        case climate::CLIMATE_MODE_DRY: gm = MODE_DRY; break;
        case climate::CLIMATE_MODE_FAN_ONLY: gm = MODE_FAN; break;
        case climate::CLIMATE_MODE_HEAT: gm = MODE_HEAT; break;
        default: break;
      }
      if (gm != 0 && gm != this->gree_mode_) this->parent_->write(this->address_, TYPE_SETTINGS, 0, &gm, 1);
      if (!this->power_) {
        uint8_t on = 1;
        this->parent_->write(this->address_, TYPE_POWER, 0, &on, 1);
      }
    }
  }
  if (call.get_target_temperature().has_value()) {
    uint16_t v = static_cast<uint16_t>(std::lround(*call.get_target_temperature() * 10.0f));
    uint8_t le[2] = {static_cast<uint8_t>(v & 0xFF), static_cast<uint8_t>(v >> 8)};
    this->parent_->write(this->address_, TYPE_SETPOINT, 0, le, 2);
  }
  uint8_t fan = 0;
  if (call.get_fan_mode().has_value()) {
    switch (*call.get_fan_mode()) {
      case climate::CLIMATE_FAN_AUTO: fan = FAN_AUTO; break;
      case climate::CLIMATE_FAN_LOW: fan = FAN_LOW; break;
      case climate::CLIMATE_FAN_MEDIUM: fan = FAN_MEDIUM; break;
      case climate::CLIMATE_FAN_HIGH: fan = FAN_HIGH; break;
      default: break;
    }
  } else if (call.has_custom_fan_mode()) {
    if (call.get_custom_fan_mode() == FAN_NAME_VERY_LOW) fan = FAN_VERY_LOW;
    else if (call.get_custom_fan_mode() == FAN_NAME_VERY_HIGH) fan = FAN_VERY_HIGH;
  }
  if (fan != 0) this->parent_->write(this->address_, TYPE_SETTINGS, 1, &fan, 1);
  if (call.get_swing_mode().has_value()) {
    auto s = *call.get_swing_mode();
    bool v = s == climate::CLIMATE_SWING_BOTH || s == climate::CLIMATE_SWING_VERTICAL;
    bool h = s == climate::CLIMATE_SWING_BOTH || s == climate::CLIMATE_SWING_HORIZONTAL;
    uint8_t sw[2] = {static_cast<uint8_t>(v ? SWING_ON : SWING_OFF), static_cast<uint8_t>(h ? SWING_ON : SWING_OFF)};
    this->parent_->write(this->address_, TYPE_SETTINGS, 2, sw, 2);
  }
  // No optimistic publish: the unit re-broadcasts the affected register within ~300 ms and that
  // is what we show. A refused change (e.g. heat while the outdoor unit cools) therefore never
  // appears as accepted.
}

}  // namespace esphome::gree_gmv
