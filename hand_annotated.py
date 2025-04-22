import argparse
import os

import cv2
import matplotlib.pyplot as plt
import numpy as np


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


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='')
    parser.add_argument("--image_path", type=str, required=True)
    parser.add_argument("--event", type=int)
    args = parser.parse_args()

    file_name, ext = os.path.splitext(args.image_path)
    label_path = f"{args.image_path}/pos.txt"
    label = np.loadtxt(label_path)
    print(label)
    for b in range(2):
            if b == 0:
                 path = 'nobacklight'
            else:
                 path = 'backlight'
            for i in range(128):
                img = cv2.imread(f'{args.image_path}/{path}/{i:03d}.jpg', -1)[:, :, ::-1]

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

                x = ref_Lab[:, 0]
                y = orig_Lab[:, 0]
                # axs[1].scatter(x, y, c=color)

                orig_gray_Lab = orig_Lab[18:]
                ref_gray_lab = ref_Lab[18:]

                x = ref_gray_lab[:, 0]
                y = orig_gray_Lab[:, 0]
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
                corrected_rgb = np.dot(orig_rgb, C)
                print("Color matrix")
                print(C)

                np.savez(f'{args.image_path}/{path}/{i:03d}.npz', orig_rgb=orig_rgb, ref_rgb=ref_rgb, orig_Lab=orig_Lab, ref_Lab=ref_Lab, color_matrix_lstsq=C)

                # fig2, ax = plt.subplots(nrows=4, sharex="all", figsize=(16, 4))
                # ax[0].imshow(orig_rgb[np.newaxis])
                # ax[0].set_title("Original")
                # ax[1].imshow(ref_rgb[np.newaxis])
                # ax[1].set_title('Reference')
                # ax[2].imshow(corrected_rgb[np.newaxis])
                # ax[2].set_title('Corrected')
                # ax[0].axis("off")
                # ax[1].axis("off")
                # ax[2].axis("off")

                # err_orig = abs(orig_rgb - ref_rgb).mean(axis=1)
                # err_corrected = abs(corrected_rgb - ref_rgb).mean(axis=1)
                # ax[3].bar(range(24), err_orig, color="red")
                # ax[3].bar(range(24), err_corrected, color="blue")

                # plt.show()
        
        # python .\hand_annotated.py --image "\\poplin.cvl.ist.osaka-u.ac.jp\share\2023\projects\tekijuku3d\capture_data\230518_P01_01\color_checker\color_checker_01\EOS01_proc\median\v00000000_l99999999.tiff"
        # python .\hand_annotated.py --image "\\poplin.cvl.ist.osaka-u.ac.jp\share\2023\projects\tekijuku3d\capture_data\230518_P01_01\color_checker\color_checker_02\EOS02_proc\median\v00000002_l99999999.tiff"
        # python .\hand_annotated.py --image "\\poplin.cvl.ist.osaka-u.ac.jp\share\2023\projects\tekijuku3d\capture_data\230518_P01_01\color_checker\color_checker_02\FLIR01\eari_proc\median\v00000000_l99999999.png"
