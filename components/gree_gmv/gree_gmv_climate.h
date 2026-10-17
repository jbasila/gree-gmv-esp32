#pragma once

#include "esphome/components/climate/climate.h"
#include "esphome/core/component.h"
#include "gree_gmv.h"

namespace esphome::gree_gmv {

class GreeGMVClimate : public climate::Climate, public Component, public GreeGMVUnit {
 public:
  void set_parent(GreeGMV *parent) { this->parent_ = parent; }
  void set_address(uint16_t address) { this->address_ = address; }
  uint16_t get_address() const override { return this->address_; }

  void setup() override;
  void dump_config() override;
  void on_message(const Message &msg) override;

 protected:
  climate::ClimateTraits traits() override;
  void control(const climate::ClimateCall &call) override;
  void publish_from_bus_();

  GreeGMV *parent_{nullptr};
  uint16_t address_{0};

  bool power_{false};
  uint8_t gree_mode_{MODE_COOL};
  uint8_t gree_fan_{FAN_AUTO};
  uint8_t swing_v_{SWING_OFF};
  uint8_t swing_h_{SWING_OFF};
  float min_temp_{16.0f};
  float max_temp_{30.0f};
};

}  // namespace esphome::gree_gmv
