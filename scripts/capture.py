import os
import time
import PySpin
from cvl_camera_controller.flir.flir_spinnaker_controller import FlirSpinnakerController, FlirCameraConfig, BaseConfig


def capture(output, ser1, ser2,  exposure=0.35):
    camera = FlirSpinnakerController(name="63S4C", workdir=output)
    exposure = exposure

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

    camera.workdir = output
    os.makedirs(camera.workdir, exist_ok=True)
    for i in range(2):
        if i == 1:
            ser2.write(bytes('a', 'utf-8'))
            print("backlight on")
            time.sleep(2)
            # exposure = 0.15
            for j in range(128):
                print(f"event {j}")
                ser1.write(bytes('a', 'utf-8'))
                time.sleep(3)
                path = camera.capture(dst_name_prefix=f"{128*i+j:03d}".format(0))

    print('Capture Completed.')
    camera.close()
