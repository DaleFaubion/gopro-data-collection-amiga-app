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

image_path = os.path.join("~/ingest", "raw_images")
image_out_path = f_org.get_image_path(vineyard, block, date)

label_path = f_org.get_label_path(vineyard, block, date)
label_file = os.path.join(label_path, "locations.csv")
labels = pd.read_csv(label_file[["name", "angle"]])

print(image_path)
print(image_out_path)
print(labels.head())
