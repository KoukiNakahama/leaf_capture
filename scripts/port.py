import serial
import serial.tools.list_ports

def select_port(baudrate=9600):
    ser = serial.Serial()
    ser.baudrate = baudrate    
    ser.timeout = None       # タイムアウトの時間

    ports = serial.tools.list_ports.comports()    # ポートデータを取得
    devices = [info.device for info in ports]

    if len(devices) == 0:
        # シリアル通信できるデバイスが見つからなかった場合
        print("エラー: ポートが見つかりませんでした")
        return None
    elif len(devices) == 1:
        print(f"一つだけポートがありました {devices[0]}")
        ser.port = devices[0]
    else:
        # 複数ポートの場合、選択
        for i in range(len(devices)):
            print(f"input {i:d} open {devices[i]}")
        num = int(input("ポート番号を入力してください:" ))
        ser.port = devices[num]
    
    # 開いてみる
    try:
        ser.open()
        return ser
    except:
        print("エラー：ポートが開けませんでした。")
        return None