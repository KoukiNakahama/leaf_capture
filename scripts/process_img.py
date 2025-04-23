import numpy as np
from PIL import Image
import os
import glob

def process_img(dir, color_matrix, scale):
    files = glob.glob(f'{dir}/*.png')
    if len(files) == 0:
        return
    for idx, file in enumerate(files):
        img = Image.open(file)
        img = img.convert("RGB")
        img_array = np.array(img, dtype=np.float32)
        img_array = img_array @ color_matrix
        img_array = np.clip(img_array, 0, 255).astype(np.uint8)
        corrected_img = Image.fromarray(img_array)
        size = (round(img.width * scale), round(img.height * scale))
        resized_img = corrected_img.resize(size)
        resized_img.save(f'{dir}/{idx:03d}.jpg')
        os.remove(file)