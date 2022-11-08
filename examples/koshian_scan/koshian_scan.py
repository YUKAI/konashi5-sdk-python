#!/usr/bin/env python3

from konashi import Konashi, KonashiScanner
import logging
import asyncio
import argparse


async def main(duration):
    try:
        logging.info("Scan for Koshian for {} seconds".format(duration))
        ks = await KonashiScanner.search(duration)
        logging.info("Number of Koshian devices discovered: {}".format(len(ks)))
        for k in ks:
            logging.info("  {}".format(k.name))
    except (asyncio.CancelledError, KeyboardInterrupt):
        logging.info("Stop loop")
    except Exception as e:
        logging.error("Exception during main loop: {}".format(e))
        raise e
    finally:
        pass
    logging.info("Exit")

async def main_forever():
    try:
        ks = KonashiScanner()
        def scan_cb(k: Konashi) -> None:
            logging.info("  {}".format(k.name))
        logging.info("Scan for Koshian devices")
        await ks.scan_start(scan_cb)
        while True:
            await asyncio.sleep(60)
    except (asyncio.CancelledError, KeyboardInterrupt):
        logging.info("Stop loop")
    except Exception as e:
        logging.error("Exception during main loop: {}".format(e))
        raise e
    finally:
        await ks.scan_stop()
    logging.info("Exit")


parser = argparse.ArgumentParser(description="Scan for Koshian devices and print the discovered list.")
parser.add_argument("DUR", type=float, nargs='?', help="The number of seconds to scan for")
args = parser.parse_args()

logging.basicConfig(level=logging.INFO)

loop = asyncio.get_event_loop()
main_task = None
try:
    if args.DUR is not None:
        main_task = loop.create_task(main(args.DUR))
    else:
        main_task = loop.create_task(main_forever())
    loop.run_until_complete(main_task)
except KeyboardInterrupt:
    if main_task is not None:
        main_task.cancel()
        loop.run_until_complete(main_task)
        main_task.exception()
finally:
    loop.close()
