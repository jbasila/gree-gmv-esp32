"""Gree GMV5 VRF over CAN bus — hub component."""

import esphome.codegen as cg
from esphome.components.canbus import CONF_CANBUS_ID, CanbusComponent
import esphome.config_validation as cv
from esphome.const import CONF_ID

CODEOWNERS = ["@jbasila"]
DEPENDENCIES = ["canbus"]

CONF_GREE_GMV_ID = "gree_gmv_id"

gree_gmv_ns = cg.esphome_ns.namespace("gree_gmv")
GreeGMV = gree_gmv_ns.class_("GreeGMV", cg.Component)

CONFIG_SCHEMA = cv.Schema(
    {
        cv.GenerateID(): cv.declare_id(GreeGMV),
        cv.GenerateID(CONF_CANBUS_ID): cv.use_id(CanbusComponent),
    }
).extend(cv.COMPONENT_SCHEMA)


async def to_code(config):
    var = cg.new_Pvariable(config[CONF_ID])
    await cg.register_component(var, config)
    bus = await cg.get_variable(config[CONF_CANBUS_ID])
    cg.add(var.set_canbus(bus))
