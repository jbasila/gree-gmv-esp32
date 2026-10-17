#!/usr/bin/env python3
"""Print climate entity states from an ESPHome device over the native API for N seconds.
usage: states.py <host> [seconds]   (run with the esphome-dev venv python)
"""
import asyncio, sys, aioesphomeapi

async def main(host, secs):
    api = aioesphomeapi.APIClient(host, 6053, None)
    await api.connect(login=True)
    ents, _ = await api.list_entities_services()
    names = {e.key: e.name for e in ents}
    seen = {}
    def on_state(st):
        if type(st).__name__ == 'ClimateState':
            seen[st.key] = st
    api.subscribe_states(on_state)
    await asyncio.sleep(secs)
    for key, st in seen.items():
        print(f"{names.get(key, key):12} mode={st.mode.name:9} fan={getattr(st,'fan_mode',None) and st.fan_mode.name:7} "
              f"custom_fan={st.custom_fan_mode!r:12} swing={st.swing_mode.name:10} target={st.target_temperature:5.1f} current={st.current_temperature:5.1f}")
    await api.disconnect()

asyncio.run(main(sys.argv[1], float(sys.argv[2]) if len(sys.argv) > 2 else 10))
