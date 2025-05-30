#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2022 Hiroaki Santo
# BalanceRatio Red:2.48, Blue:0.98

import argparse
import time
import os
import numpy as np

from scripts.capture import capture
from scripts.port import select_port
from scripts.process_img import process_img
from scripts.calc_color_matrix import image_point_annotator, hand_annotated

parser = argparse.ArgumentParser()
parser.add_argument('--output', default='test', help='保存先のフォルダ')
parser.add_argument('--exposure', default=0.35)
parser.add_argument('--width', default=512)
parser.add_argument('--height', default=512)
parser.add_argument('--hand_annotation', action='store_true')
parser.add_argument('--overwrite', action='store_true')
args = parser.parse_args()

def main():
    output = f'./imgs/{args.output}'
    exposure = args.exposure
    width = args.width
    height = args.height
    hand_annotation = args.hand_annotation
    if args.overwrite == False:
        assert not os.path.exists(output), "This folder already exists!"
        
    # マイコンと接続
    ser1 = select_port(9600) # 上側のライト
    assert ser1 != None, 'ser1 is None'
    ser2 = select_port(9600) # 下側のライト
    assert ser2 != None, 'ser2 is None'
    time.sleep(3)

    # 画像撮影
    capture(output, ser1, ser2, exposure)
    
    # マイコンを切断
    ser1.close()
    ser2.close()
    
    # 色補正行列を出力(任意)
    if hand_annotation:
        image_point_annotator()
        hand_annotated()
    
    # 画像の前処理(拡張子変換，色補正，リサイズ)
    process_img(output, width, height)
    
    print('Finish.')

if __name__ == '__main__':
    main()