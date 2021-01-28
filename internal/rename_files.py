# Fall 2020
# Vinetech Image Renaming
# Ingest Step 4

from .common import *
import pandas as pd
import os


def main(f_org, args, df=None):
    """
    main adds the relative path to the image from images directory.
    """

    # Open the current csv
    label_file = f_org.get_label_file(args.vineyard, args.block, args.date)
    if df is None:
        df = pd.read_csv(label_file, index_col=False)

    print("Renaming column instead of moving files for now")
    img_dir = f_org.get_image_path(args.vineyard, args.block, args.date)
    df["name"] = df["raw_dir"].apply(
        lambda x: x[x.find(args.date) + len(args.date) + 1 :]
    )

    link_name = os.path.join(f_org.home, "images")
    df["raw_dir"] = df["raw_dir"].apply(
        lambda x: x.replace(link_name, os.readlink(link_name))
    )

    df[columns].to_csv(label_file)
    return df[columns]
