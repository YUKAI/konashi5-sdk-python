#!/usr/bin/env python3
# 加速度センサの値を表示するサンプルプログラム
from konashi import *
from konashi.Io.GPIO import *
from konashi.Builtin import *
import asyncio

# 接続するkonashiの名前
KONASHI_NAME = "ksXXXXXX"

# 加速度の表示
def accel_check(accel: Tuple[float, float, float], gyro: Tuple[float, float, float]):
    print("Acceleration: x={:.2f}g, y={:.2f}g, z={:.2f}g".format(accel[0], accel[1], accel[2]))
    print("Gyroscope: x={:.2f}°/s, y={:.2f}°/s, z={:.2f}°/s".format(gyro[0], gyro[1], gyro[2]))

async def main():
    k = Konashi(KONASHI_NAME)
    # 接続する(タイムアウト5秒)
    await k.connect(5)

    await k.builtin.accelgyro.set_callback(accel_check)

    while True:
        await asyncio.sleep(0.5)

main_task = None
try:
    # main関数を実行
    main_task = asyncio.run(main())
except KeyboardInterrupt:
    # Ctrl+Cで終了
    main_task.cancel()