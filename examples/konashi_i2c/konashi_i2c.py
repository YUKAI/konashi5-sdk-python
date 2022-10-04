#!/usr/bin/env python3

from asyncio.exceptions import CancelledError
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


        # enable I2C in standard mode
        await device.io.i2c.config(konashi.I2CConfig(True, konashi.I2CMode.STANDARD))

        sens_addr = 0x11
        cnt = 0
        while True:
            res, addr, data = await device.io.i2c.transaction(konashi.I2COperation.WRITE, sens_addr, 0, [cnt, 0x10, 0x50])
            print("Result:", res, "Address:", addr, "Data:", data)
            res, addr, data = await device.io.i2c.transaction(konashi.I2COperation.READ, sens_addr, 5, [])
            print("Result:", res, "Address:", addr, "Data:", data)
            await asyncio.sleep(5)
            cnt += 1
            cnt %= 0xFF


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


parser = argparse.ArgumentParser(description="Connect to a konashi device, setup I2C and read from a VL6180X sensor.")
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