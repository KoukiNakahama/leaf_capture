#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2022 Hiroaki Santo
# BalanceRatio Red:2.48, Blue:0.98

import PySpin
import cv2
import serial
import serial.tools.list_ports
import argparse
import time
import os
from port import select_port

from cvl_camera_controller.flir.flir_spinnaker_controller import FlirSpinnakerController, FlirCameraConfig, BaseConfig

def capture(i, output, exposure):
    camera = FlirSpinnakerController(name="63S4C", workdir=output)

    camera.set_config({FlirCameraConfig.PIXEL_FORMAT: PySpin.PixelFormat_BayerRG16})
    camera.connect()
    try:
        camera.set_config({BaseConfig.ALL_MANUAL: True})
        camera.set_config({BaseConfig.EXPOSURE_TIME_SEC: exposure})
        current_exposure_time_ms = camera.get_config([FlirCameraConfig.SHUTTER_SPEED])[FlirCameraConfig.SHUTTER_SPEED]
        # assert abs(current_exposure_time_ms - 500) < 0.1, current_exposure_time_ms
        print(current_exposure_time_ms)

        path = camera.capture(dst_name_prefix=f"{i:03d}".format(0))
        print(path)

    finally:
        camera.close()

    # p = path[0]
    # print(p)
    # img = cv2.imread(p, -1)
    # print(img.shape, img.dtype, img.min(), img.max())

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('output', type=str, help='保存先のフォルダ')
    parser.add_argument('--overwrite', type=bool, default=False)
    parser.add_argument('--pattern', type=int, default=1)
    args = parser.parse_args()
    output = f'./imgs/{args.output}'
    overwrite = args.overwrite
    pattern = args.pattern
    if overwrite == False:
        assert not os.path.exists(output), "This folder already exists!"
    ser1 = select_port(9600) # 上側のライト
    assert ser1 != None, 'ser1 is None'
    ser2 = select_port(9600) # 下側のライト
    assert ser2 != None, 'ser2 is None'
    print("start")
    time.sleep(3)

    camera = FlirSpinnakerController(name="63S4C", workdir=output)
    exposure = 0.35 # pattern 1
    # exposure = 0.50 # pattern 2

    camera.set_config({FlirCameraConfig.PIXEL_FORMAT: PySpin.PixelFormat_BayerRG16})
    camera.connect()
    camera.camera_list[0].EndAcquisition()
    # フレームの最大取得数の設定
    nodemap = camera.camera_list[0].GetNodeMap()
    node_frame_count = PySpin.CIntegerPtr(nodemap.GetNode('AcquisitionFrameCount'))
    node_frame_count.SetValue(node_frame_count.GetMax())
    # 最新のフレームを送信するように設定
    s_node_map = camera.camera_list[0].GetTLStreamNodeMap()
    handling_mode = PySpin.CEnumerationPtr(s_node_map.GetNode('StreamBufferHandlingMode'))
    handling_mode_entry = handling_mode.GetEntryByName('NewestOnly')
    handling_mode.SetIntValue(handling_mode_entry.GetValue())
    camera.camera_list[0].BeginAcquisition()
    camera.set_config({BaseConfig.ALL_MANUAL: True})
    camera.set_config({BaseConfig.EXPOSURE_TIME_SEC: exposure})
    current_exposure_time_ms = camera.get_config([FlirCameraConfig.SHUTTER_SPEED])[FlirCameraConfig.SHUTTER_SPEED]
    # assert abs(current_exposure_time_ms - 500) < 0.1, current_exposure_time_ms
    print(current_exposure_time_ms)

    if pattern == 1:
        camera.workdir = os.path.join(output, "nobacklight")
        os.makedirs(camera.workdir, exist_ok=True)
        for i in range(2):
            if i == 1:
                ser2.write(bytes('a', 'utf-8'))
                print("backlight on")
                camera.workdir = os.path.join(output, "backlight")
                os.makedirs(camera.workdir, exist_ok=True)
                time.sleep(2)
                # exposure = 0.15
            for j in range(10):
                print(f"event {j}")
                ser1.write(bytes('a', 'utf-8'))
                time.sleep(1)
                if i == 0 and j == 9:
                    continue
                path = camera.capture(dst_name_prefix=f"{j:03d}".format(0))
                print(path)

    if pattern == 2:
        camera.workdir = os.path.join(output, "nobacklight")
        os.makedirs(camera.workdir, exist_ok=True)
        for i in range(2):
            if i == 1:
                ser2.write(bytes('a', 'utf-8'))
                print("backlight on")
                camera.workdir = os.path.join(output, "backlight")
                os.makedirs(camera.workdir, exist_ok=True)
                time.sleep(2)
                # exposure = 0.15
            for j in range(128):
                print(f"event {j}")
                ser1.write(bytes('a', 'utf-8'))
                time.sleep(3)
                path = camera.capture(dst_name_prefix=f"{j:03d}".format(0))
                print(path)
        
            
    ser1.close()
    ser2.close()
    print('finish')

    camera.close()
