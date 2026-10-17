"""One climate entity per Gree GMV indoor unit."""

import esphome.codegen as cg
from esphome.components import climate
import esphome.config_validation as cv
from esphome.const import CONF_ADDRESS

from . import CONF_GREE_GMV_ID, GreeGMV, gree_gmv_ns

DEPENDENCIES = ["gree_gmv"]

GreeGMVClimate = gree_gmv_ns.class_("GreeGMVClimate", climate.Climate, cg.Component)


def _node_address(value):
    value = cv.hex_uint16_t(value)
    if value & 0x7F:
        raise cv.Invalid(
            "address must be a node base (multiple of 0x80), e.g. 0xD000, 0xD080, 0xD100 ..."
        )
    return value


CONFIG_SCHEMA = (
    climate.climate_schema(GreeGMVClimate)
    .extend(
        {
            cv.GenerateID(CONF_GREE_GMV_ID): cv.use_id(GreeGMV),
            cv.Required(CONF_ADDRESS): _node_address,
        }
    )
    .extend(cv.COMPONENT_SCHEMA)
)


async def to_code(config):
    var = await climate.new_climate(config)
    await cg.register_component(var, config)
    hub = await cg.get_variable(config[CONF_GREE_GMV_ID])
    cg.add(var.set_parent(hub))
    cg.add(var.set_address(config[CONF_ADDRESS]))
    cg.add(hub.register_unit(var))
