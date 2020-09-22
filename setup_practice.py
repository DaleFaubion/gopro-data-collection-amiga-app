#

# Fall 2020
# Vinetech ingest practice setup

import os
import pandas as pd

import __init__
from organization import file_org as f_org

date = "2019-07-31"
vineyard = "crawford-beck"
block = 9

image_path = f_org.ensure_path("~/ingest", "raw_images")
image_out_path = f_org.get_image_path(vineyard, block, date)

label_path = f_org.get_label_path(vineyard, block, date)
label_file = os.path.join(label_path, "locations.csv")
labels = pd.read_csv(label_file)

x = 0


def make_symlinks(angle, dirname):

    for image in labels.loc[labels["angle"] == angle, "name"]:
        os.symlink(
            os.path.join(image_out_path, image),
            os.path.join(image_path, dirname, str(x) + ".jpg"),
        )

        x += 1


make_symlinks(0, "top_camera")
make_symlinks(1, "bottom_camera")
make_symlinks(2, "middle_camera")
