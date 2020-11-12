#

#

from .common import *
import pandas as pd
import os


def main(f_org, args, df=None):

    # Open the current csv
    label_file = f_org.get_label_file(args.vineyard, args.block, args.date)
    if df is None:
        df = pd.read_csv(label_file, index_col=False)

    print("Renaming column instead of moving files for now")
    img_dir = f_org.get_image_path(args.vineyard, args.block, args.date)
    df["name"] = df["raw_dir"].apply(lambda x: x[x.find("raw_images") + 11 :])

    df[columns].to_csv(label_file)
    return df[columns]
