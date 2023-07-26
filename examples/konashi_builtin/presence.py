#!/usr/bin/env python3
# 人感センサで動きを検知するサンプルプログラム
from konashi import *
from konashi.Io.GPIO import *
from konashi.Builtin import *
import asyncio

# 接続するkonashiの名前
KONASHI_NAME = "ksXXXXXX"

# 人感センサでの検知
def presence_check(presence):
    if presence:
        print("Presence detected!")
    else:
        print("No presence detected.")

async def main():
    k = Konashi(KONASHI_NAME)
    # 接続する(タイムアウト5秒)
    await k.connect(5)

    await k.builtin.presence.set_callback(presence_check)

    while True:
        await asyncio.sleep(0.5)

main_task = None
try:
    # main関数を実行
    main_task = asyncio.run(main())
except KeyboardInterrupt:
    # Ctrl+Cで終了
    main_task.cancel()