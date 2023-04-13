#!/usr/bin/env python3
# 気圧を表示するサンプルプログラム
from konashi import *
from konashi.Io.GPIO import *
from konashi.Builtin import *
import asyncio

# 接続するkonashiの名前
KONASHI_NAME = "ksXXXXXX"

# 気圧の表示
def pressure_check(pressure: float):
    print("Pressure: {}".format(pressure))

async def main():
    k = Konashi(KONASHI_NAME)
    # 接続する(タイムアウト5秒)
    await k.connect(5)

    await k.builtin.pressure.set_callback(pressure_check)

    while True:
        await asyncio.sleep(0.5)

main_task = None
try:
    # main関数を実行
    main_task = asyncio.run(main())
except KeyboardInterrupt:
    # Ctrl+Cで終了
    main_task.cancel()