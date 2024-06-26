#!/usr/bin/env python3

from asyncio.exceptions import CancelledError
import re
from tkinter.messagebox import NO
from konashi import *
import konashi
import logging
import asyncio
import argparse


async def main(device):
    try:
        if device is None:
            logging.info("Scan for konashi devices for 5 seconds")
            ks = await KonashiScanner.search(5)
            if len(ks) > 0:
                device = ks[0]
                logging.info("Use konashi device: {}".format(device.name))
            else:
                logging.error("Could no find a konashi device")
                return
        try:
            await device.connect(5)
        except Exception as e:
            logging.error("Could not connect to konashi device '{}': {}".format(device.name, e))
            return
        logging.info("Connected to device")

        def temperature_callback(temperature: float) -> None:
            print("Temperature: {}degC".format(temperature))
        await device.builtin.temperature.set_callback(temperature_callback)

        def humidity_callback(humidity: float) -> None:
            print("Humidity: {}%".format(humidity))
        await device.builtin.humidity.set_callback(humidity_callback)

        def pressure_callback(pressure: float) -> None:
            print("Pressure: {}hPa".format(pressure))
        await device.builtin.pressure.set_callback(pressure_callback)

        def presence_callback(presence: bool) -> None:
            print("Presence: {}".format(presence))
        await device.builtin.presence.set_callback(presence_callback)

        while True:
            await asyncio.sleep(10)


    except (asyncio.CancelledError, KeyboardInterrupt):
        logging.info("Stop loop")
    except Exception as e:
        logging.error("Exception during main loop: {}".format(e))
        raise e
    finally:
        try:
            if device is not None:
                await device.disconnect()
                logging.info("Disconnected")
        except konashi.Errors.KonashiConnectionError:
            pass
    logging.info("Exit")


parser = argparse.ArgumentParser(description="Connect to a konashi device and use builtin environment sensors.")
parser.add_argument("--device", "-d", type=Konashi, help="The konashi device name to use. Ommit to scan and use first discovered device.")
args = parser.parse_args()

logging.basicConfig(level=logging.INFO)

loop = asyncio.get_event_loop()
main_task = None
try:
    main_task = loop.create_task(main(args.device))
    loop.run_until_complete(main_task)
except KeyboardInterrupt:
    if main_task is not None:
        main_task.cancel()
        loop.run_until_complete(main_task)
        main_task.exception()
finally:
    loop.close()