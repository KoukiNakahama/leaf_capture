import numpy as np
from PIL import Image
import os
import glob

def crop_center(pil_img, crop_width, crop_height):
    img_width, img_height = pil_img.size
    return pil_img.crop(((img_width - crop_width) // 2,
                         (img_height - crop_height) // 2,
                         (img_width + crop_width) // 2,
                         (img_height + crop_height) // 2))

def process_img(dir, width, height):
    paths = glob.glob(f'{dir}/*.png')
    if len(paths) == 0:
        return
    for idx, path in enumerate(paths):
        file, ext = os.path.splitext(path)
        img = Image.open(path)
        img = img.convert("RGB")
        img_array = np.array(img, dtype=np.float32)
        color_matrix = np.load(f'{file}.npz')['color_matrix_lstsq']
        img_array = img_array @ color_matrix
        img_array = np.clip(img_array, 0, 255).astype(np.uint8)
        corrected_img = Image.fromarray(img_array)
        resized_img = crop_center(corrected_img, width, height)
        resized_img.save(f'{file}.jpg')
        os.remove(path)