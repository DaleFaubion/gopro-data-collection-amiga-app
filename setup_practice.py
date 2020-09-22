#

# Fall 2020
# Vinetech ingest practice setup

import os
import pandas as pd
import shutil

import __init__
from organization import file_org as f_org

date = "2019-07-31"
vineyard = "crawford-beck"
block = 9

image_path = f_org.ensure_path(f_org.home + "/ingest", "raw_images")
image_out_path = f_org.get_image_path(vineyard, block, date)

label_path = f_org.get_label_path(vineyard, block, date)
label_file = os.path.join(label_path, "locations.csv")
labels = pd.read_csv(label_file)

x = 0


def copy_images(angle, dirname, x):

    dirname = os.path.join(image_path, dirname)
    if not os.path.isdir(dirname):
        os.makedirs(dirname)

    for image in labels.loc[labels["angle"] == angle, "name"]:
        filename = os.path.join(dirname, str(x) + ".JPG")
        realfile = os.path.join(image_out_path, image)
        print(realfile, filename)
        if os.path.isfile(filename):
            os.remove(filename)
        os.symlink(realfile, filename)

        x += 1

    return x


x = copy_images(0, "top_camera", x)
x = copy_images(1, "bottom_camera", x)
x = copy_images(2, "middle_camera", x)
