import glob
import os
import argparse

import cv2
import numpy as np
import matplotlib.pyplot as plt

loop_true = True

def labeling_2d_point_with_matplotlib(img):
    m, n, _ = img.shape
    img = img.copy()

    global loop_true
    clicked_point = []

    last_clicked_pt = (np.array([0., 0.]))

    fig = plt.figure()

    def __onclick(event):
        print(event.xdata, event.ydata)
        last_clicked_pt[:] = np.array((event.xdata, event.ydata))

    def __onkey(event):
        if event.key == ' ':
            print("saved: {}".format(last_clicked_pt))
            clicked_point.append(last_clicked_pt.copy())
            pt = tuple(last_clicked_pt.astype(int))
            cv2.circle(img, pt, 5, (0, 0, 255), 1)
            plt.xlim(0, n)
            plt.ylim(m, 0)

        elif event.key == 'q':
            global loop_true
            loop_true *= False

    cid = fig.canvas.mpl_connect('button_press_event', __onclick)
    cid = fig.canvas.mpl_connect('key_press_event', __onkey)

    fig_im = plt.imshow(img, interpolation='nearest')
    while loop_true != 0:
        # plt.cla()
        fig_im.set_data(img)
        plt.pause(0.1)

    plt.close()
    loop_true += True

    return np.array(clicked_point)


def image_point_annotator():
    parser = argparse.ArgumentParser(description='')
    parser.add_argument("--dir_path", type=str)
    parser.add_argument("--filename_format", type=str, default="*.jpg")
    parser.add_argument("--output_suffix", type=str, default="_labeling_manual")

    args = parser.parse_args()
    dir_path = args.dir_path

    paths = glob.glob(os.path.join(dir_path, args.filename_format))
    for i, path in enumerate(paths):
        print("{}/{}, {}".format(i + 1, len(paths), path))
        file_name, ext = os.path.splitext(os.path.basename(path))
        o_path = os.path.join(dir_path, f"{file_name}{args.output_suffix}.txt")
        if os.path.exists(o_path):
            print("[!] {} already exists.".format(o_path))
            continue

        img = cv2.imread(path)[:, :, ::-1]
        point = labeling_2d_point_with_matplotlib(img)
        print(point, point.shape)
        if len(point) == 0:
            print("[!] SKIP")
        else:
            np.savetxt(o_path, point)
