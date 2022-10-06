#!/usr/bin/env python3

from asyncio.exceptions import CancelledError
from konashi import *
import konashi
from konashi.Io import Analog as KonashiAnalog
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


        # set analog input callback
        def input_cb(pin, val):
            logging.info("Ain{}: {:.2f}V".format(pin, val))
        device.io.analog.set_input_cb(input_cb)

        # setup ADC read period to 0.5s, ref to VDD (3.3V) and enable all pins as input
        await device.io.analog.config_adc_period(0.5)
        await device.io.analog.config_adc_ref(KonashiAnalog.AdcRef.REF_VDD)
        await device.io.analog.config_pins([(0x07, KonashiAnalog.PinConfig(True, KonashiAnalog.PinDirection.INPUT, True))])

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
        except konashi.Errors.KonashiConnectionError:
            pass
    logging.info("Exit")


parser = argparse.ArgumentParser(description="Connect to a konashi device, setup analog inputs and read the inputs.")
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