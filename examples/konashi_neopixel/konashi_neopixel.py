#!/usr/bin/env python3


import logging
import asyncio
import argparse
from time import sleep
from konashi import Konashi, Errors as KonashiErrors
from konashi.Io.NeoPixel import NeoPixelConfig, NeoPixelLedOutput


async def main(device):
    try:
        if device is None:
            logging.info("Scan for konashi devices for 5 seconds")
            ks = await Konashi.search(5)
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


        await device.io.neopixel.config(NeoPixelConfig(True, 0, 3))
        await asyncio.sleep(2)
        await device.io.neopixel.control_leds([(0, NeoPixelLedOutput(255,0,0,500)),(1, NeoPixelLedOutput(0,255,0,500)),(2, NeoPixelLedOutput(0,0,255,500))])

        while True:
            await asyncio.sleep(100)


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
        except KonashiErrors.KonashiConnectionError:
            pass
    logging.info("Exit")



parser = argparse.ArgumentParser(description="Connect to a konashi device, setup analog inputs and read the inputs.")
parser.add_argument("--device", "-d", type=Konashi, help="The konashi device name to use. Ommit to scan and use first discovered device.")
args = parser.parse_args()

logging.basicConfig(level=logging.INFO)
logging.getLogger("konashi").setLevel(logging.DEBUG)

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
