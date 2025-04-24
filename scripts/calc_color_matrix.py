import os
import cv2
import matplotlib.pyplot as plt
import numpy as np
import glob

loop_true = True

def _get_colorchecker_reference():
    # https://babelcolor.com/index_htm_files/ColorChecker24_After_Nov2014.txt
    ref_colors_Lab = np.array([["A1", "37.54", "14.37", "14.92"],
                               ["A2", "62.73", "35.83", "56.5"],
                               ["A3", "28.37", "15.42", "-49.8"],
                               ["A4", "95.19", "-1.03", "2.93"],
                               ["B1", "64.66", "19.27", "17.5"],
                               ["B2", "39.43", "10.75", "-45.17"],
                               ["B3", "54.38", "-39.72", "32.27"],
                               ["B4", "81.29", "-0.57", "0.44"],
                               ["C1", "49.32", "-3.82", "-22.54"],
                               ["C2", "50.57", "48.64", "16.67"],
                               ["C3", "42.43", "51.05", "28.62"],
                               ["C4", "66.89", "-0.75", "-0.06"],
                               ["D1", "43.46", "-12.74", "22.72"],
                               ["D2", "30.1", "22.54", "-20.87"],
                               ["D3", "81.8", "2.67", "80.41"],
                               ["D4", "50.76", "-0.13", "0.14"],
                               ["E1", "54.94", "9.61", "-24.79"],
                               ["E2", "71.77", "-24.13", "58.19"],
                               ["E3", "50.63", "51.28", "-14.12"],
                               ["E4", "35.63", "-0.46", "-0.48"],
                               ["F1", "70.48", "-32.26", "-0.37"],
                               ["F2", "71.51", "18.24", "67.37"],
                               ["F3", "49.57", "-29.71", "-28.32"],
                               ["F4", "20.64", "0.07", "-0.46"]]).reshape(6, 4, 4).transpose([1, 0, 2]).reshape(-1, 4)
    ref_colors_Lab = ref_colors_Lab[:, 1:].astype(float)
    return ref_colors_Lab

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


def image_point_annotator(dir_path, filename_format='*.jpg', output_suffix='pos'):
    paths = glob.glob(os.path.join(dir_path, filename_format))
    for i, path in enumerate(paths):
        print("{}/{}, {}".format(i + 1, len(paths), path))
        o_path = os.path.join(dir_path, f"{output_suffix}.txt")
        if os.path.exists(o_path):
            print("[!] {} already exists.".format(o_path))
            continue

        img = cv2.imread(path)[:, :, ::-1]
        point = labeling_2d_point_with_matplotlib(img)
        print(point, point.shape)
        if len(point) == 0:
            print("[!] SKIP")
            break
        else:
            np.savetxt(o_path, point)

def hand_annotated(image_path):
    label_path = f"{image_path}/pos.txt"
    label = np.loadtxt(label_path)
    print(label)
    paths = glob.glob(os.path.join(image_path, '*.jpg'))
    for i, path in enumerate(paths):
        file, ext = os.path.splitext(path)
        img = cv2.imread(path, -1)[:, :, ::-1]

        print(img.shape)

        color = []
        for pt in label:
            pt = np.round(pt).astype(int)
            color.append(img[pt[1], pt[0], :])

        color = np.array(color)
        print(color)
        color = color.astype(np.float32) / np.iinfo(color.dtype).max
        print(color)

        orig_Lab = cv2.cvtColor(color[None], cv2.COLOR_LRGB2Lab)[0]
        assert orig_Lab.shape == (24, 3), orig_Lab.shape
        # L: [0, 100]
        # a: [-127, 127]
        # b: [-127, 127]

        ref_Lab = _get_colorchecker_reference()
        assert ref_Lab.shape == orig_Lab.shape

        # fig1, axs = plt.subplots(2, 1, figsize=(6, 6))
        # Using the additional data to plot the colour checker and masks.

        # x = ref_Lab[:, 0]
        # y = orig_Lab[:, 0]
        # axs[1].scatter(x, y, c=color)

        # orig_gray_Lab = orig_Lab[18:]
        # ref_gray_lab = ref_Lab[18:]

        # x = ref_gray_lab[:, 0]
        # y = orig_gray_Lab[:, 0]
        # axs[1].plot(x, y, c="gray")
        # axs[1].set_title("Lightness in Lab color space")

        # axs[1].set_xlim(0, 100)
        # axs[1].set_ylim(0, 100)
        # axs[1].set_aspect('equal', adjustable='box')

        A = orig_Lab[np.newaxis, :, :].astype(np.float32)
        B = ref_Lab[np.newaxis, :, :].astype(np.float32)

        orig_rgb = cv2.cvtColor(A, cv2.COLOR_LAB2LRGB)[0]
        ref_rgb = cv2.cvtColor(B, cv2.COLOR_LAB2LRGB)[0]
        assert np.linalg.norm(orig_rgb - color) < 1e-4, np.linalg.norm(orig_rgb - color)

        assert orig_rgb.shape == (24, 3), orig_rgb.shape
        assert ref_rgb.shape == orig_rgb.shape, ref_rgb.shape

        print(orig_rgb.max(), ref_rgb.max())
        C = np.linalg.lstsq(orig_rgb, ref_rgb, rcond=None)[0]
        # corrected_rgb = np.dot(orig_rgb, C)
        print("Color matrix")
        print(C)

        np.savez(os.path.join(file, '.npz'), orig_rgb=orig_rgb, ref_rgb=ref_rgb, orig_Lab=orig_Lab, ref_Lab=ref_Lab, color_matrix_lstsq=C)
