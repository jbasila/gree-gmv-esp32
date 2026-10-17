#!/usr/bin/env python3
"""Press an ESPHome button by name over the native API. Run with the esphome venv python.
usage: press.py <host> "<button name>"
"""
import asyncio, sys, aioesphomeapi

async def main(host, name):
    api = aioesphomeapi.APIClient(host, 6053, None)
    await api.connect(login=True)
    ents, _ = await api.list_entities_services()
    for e in ents:
        if getattr(e, 'name', None) == name:
            api.button_command(e.key)
            print("pressed:", name)
            break
    else:
        print("no such button; have:", [getattr(e,'name',None) for e in ents])
    await asyncio.sleep(1)
    await api.disconnect()

asyncio.run(main(sys.argv[1], sys.argv[2]))
