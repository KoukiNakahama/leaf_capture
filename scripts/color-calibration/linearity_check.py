#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2022 Hiroaki Santo

import argparse
import colour
import cv2
import matplotlib.pyplot as plt
import numpy as np
import os
from colour_checker_detection import detect_colour_checkers_segmentation


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


def main():
    parser = argparse.ArgumentParser(description='color checker')
    parser.add_argument("--image_path", "-i", type=str, nargs="+", required=True)
    parser.add_argument("--output_dir", "-o", type=str, default=None)

    args = parser.parse_args()
    img_paths = args.image_path
    output_dir = args.output_dir

    if os.name == 'nt' and len(img_paths) == 1 and "*" in img_paths[0]:
        import glob
        img_paths = glob.glob(img_paths[0])

    for image_path in img_paths:
        image = colour.io.read_image(image_path, method='Imageio')
        detected = detect_colour_checkers_segmentation(image, additional_data=True)

        if len(detected) == 0:
            print("Detection failed!!", image_path)
            continue

        for colour_checker_swatches_data in detected:
            swatch_colours, colour_checker_image, swatch_masks = (colour_checker_swatches_data.values)

            swatch_colours = np.array(swatch_colours)
            orig_Lab = cv2.cvtColor(swatch_colours[None], cv2.COLOR_LRGB2Lab)[0]
            assert orig_Lab.shape == (24, 3), orig_Lab.shape
            # L: [0, 100]
            # a: [-127, 127]
            # b: [-127, 127]

            ref_Lab = _get_colorchecker_reference()
            assert ref_Lab.shape == orig_Lab.shape

            fig1, axs = plt.subplots(2, 1, figsize=(6, 6))
            # Using the additional data to plot the colour checker and masks.
            masks_i = np.zeros(colour_checker_image.shape)
            for i, mask in enumerate(swatch_masks):
                masks_i[mask[0]:mask[1], mask[2]:mask[3], ...] = 1
            detected_img = np.clip(colour_checker_image + masks_i * 0.25, 0, 1)
            axs[0].imshow(detected_img)
            axs[0].axis("off")
            axs[0].set_title("Detected pattern")

            x = ref_Lab[:, 0]
            y = orig_Lab[:, 0]
            axs[1].scatter(x, y, c=swatch_colours)

            orig_gray_Lab = orig_Lab[18:]
            ref_gray_lab = ref_Lab[18:]

            x = ref_gray_lab[:, 0]
            y = orig_gray_Lab[:, 0]
            axs[1].plot(x, y, c="gray")
            axs[1].set_title("Lightness in Lab color space")

            axs[1].set_xlim(0, 100)
            axs[1].set_ylim(0, 100)
            axs[1].set_aspect('equal', adjustable='box')

            A = orig_Lab[np.newaxis, :, :].astype(np.float32)
            B = ref_Lab[np.newaxis, :, :].astype(np.float32)

            orig_rgb = cv2.cvtColor(A, cv2.COLOR_LAB2LRGB)[0]
            ref_rgb = cv2.cvtColor(B, cv2.COLOR_LAB2LRGB)[0]
            assert orig_rgb.shape == (24, 3), orig_rgb.shape
            assert ref_rgb.shape == orig_rgb.shape, ref_rgb.shape

            C = np.linalg.lstsq(orig_rgb, ref_rgb, rcond=None)[0]
            corrected_rgb = np.dot(orig_rgb, C)
            print("Color matrix")
            print(C)

            fig2, ax = plt.subplots(nrows=4, sharex="all", figsize=(16, 4))
            ax[0].imshow(orig_rgb[np.newaxis])
            ax[0].set_title("Original")
            ax[1].imshow(ref_rgb[np.newaxis])
            ax[1].set_title('Reference')
            ax[2].imshow(corrected_rgb[np.newaxis])
            ax[2].set_title('Corrected')
            ax[0].axis("off")
            ax[1].axis("off")
            ax[2].axis("off")

            err_orig = abs(orig_rgb - ref_rgb).mean(axis=1)
            err_corrected = abs(corrected_rgb - ref_rgb).mean(axis=1)
            ax[3].bar(range(24), err_orig, color="red")
            ax[3].bar(range(24), err_corrected, color="blue")

            if output_dir is not None:
                os.makedirs(output_dir, exist_ok=True)
                file_name = os.path.basename(image_path)
                file_name, _ = os.path.splitext(file_name)

                opath = os.path.join(output_dir, file_name + "_linearity_check.png")
                fig1.savefig(opath, bbox_inches='tight', pad_inches=0)
                opath = os.path.join(output_dir, file_name + "_color_matrix.png")
                fig2.savefig(opath, bbox_inches='tight', pad_inches=0)
                plt.close(fig1)
                plt.close(fig2)
            else:
                plt.show()
                plt.close()


if __name__ == "__main__":
    main()
