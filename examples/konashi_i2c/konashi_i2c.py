#!/usr/bin/env python3

from asyncio.exceptions import CancelledError
from konashi import *
import konashi
from konashi.Io import I2C as KonashiI2C
import logging
import asyncio
import argparse


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


        # enable I2C in standard mode
        await device.io.i2c.config(KonashiI2C.Config(True, KonashiI2C.Mode.STANDARD))

        # using VL6180X sensor (https://www.pololu.com/product/2489/resources)
        sens_addr = 0x29

        # IDENTIFICATION__MODEL_ID (0x000) read
        res, addr, data = await device.io.i2c.transaction(KonashiI2C.Operation.WRITE_READ, sens_addr, 1, [0x00, 0x00])
        if res == KonashiI2C.Result.DONE:
            logging.info("IDENTIFICATION__MODEL_ID: {}".format("".join("{:02x}".format(x) for x in data)))
        else:
            logging.error("Error reading IDENTIFICATION__MODEL_ID: {}".format(res))
            return

        # RESULT__ALS_STATUS (0x04E) read
        res, addr, data = await device.io.i2c.transaction(KonashiI2C.Operation.WRITE_READ, sens_addr, 1, [0x00, 0x4E])
        if res == KonashiI2C.Result.DONE:
            logging.info("RESULT__ALS_STATUS: {}".format("".join("{:02x}".format(x) for x in data)))
        else:
            logging.error("Error reading RESULT__ALS_STATUS: {}".format(res))
            return
        if (data[0]&0x01) == 0x01:
            # set ASL intermeasurement period an integration period
            res, addr, data = await device.io.i2c.transaction(KonashiI2C.Operation.WRITE, sens_addr, 0, [0x00, 0x3E, 0x31])
            if res != KonashiI2C.Result.DONE:
                logging.error("Error writing SYSALS__INTERMEASUREMENT_PERIOD: {}".format(res))
                return
            res, addr, data = await device.io.i2c.transaction(KonashiI2C.Operation.WRITE, sens_addr, 0, [0x00, 0x17, 0x01])
            if res != KonashiI2C.Result.DONE:
                logging.error("Error writing SYSTEM__GROUPED_PARAMETER_HOLD: {}".format(res))
                return
            res, addr, data = await device.io.i2c.transaction(KonashiI2C.Operation.WRITE, sens_addr, 0, [0x00, 0x40, 0x63])
            if res != KonashiI2C.Result.DONE:
                logging.error("Error writing SYSALS__INTERMEASUREMENT_PERIOD: {}".format(res))
                return
            res, addr, data = await device.io.i2c.transaction(KonashiI2C.Operation.WRITE, sens_addr, 0, [0x00, 0x17, 0x00])
            if res != KonashiI2C.Result.DONE:
                logging.error("Error writing SYSTEM__GROUPED_PARAMETER_HOLD: {}".format(res))
                return
            # SYSALS__START (0x038) write: ALS Mode continuous, start
            res, addr, data = await device.io.i2c.transaction(KonashiI2C.Operation.WRITE, sens_addr, 0, [0x00, 0x38, 0x03])
            if res == KonashiI2C.Result.DONE:
                logging.info("SYSALS__START write done")
            else:
                logging.error("Error writing SYSALS__START: {}".format(res))
                return
        
        # read RESULT__ALS_VAL (0x050) continuously every second
        while True:
            res, addr, data = await device.io.i2c.transaction(KonashiI2C.Operation.WRITE_READ, sens_addr, 2, [0x00, 0x50])
            if res == KonashiI2C.Result.DONE:
                logging.debug("RESULT__ALS_VAL: {}".format("".join("{:02x}".format(x) for x in data)))
                lux = ((data[0]<<8)+data[1]) * 0.32 * 100/ (1.0 * 100)
                logging.info("ALS: {}lux".format(lux))
            else:
                logging.error("Error reading RESULT__ALS_VAL: {}".format(res))
                return
            await asyncio.sleep(1)


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