# Fall 2020
# Vinetech Image Ingest Script Evaluation

import os
import argparse
import shutil
import pandas as pd

from sklearn import metrics

import __init__
from organization import file_org as f_org
from internal import gen_csv, pad_csv, row_pred, bay_pred, rename_files


def parse_args():
    """
    parse_args returns the command line arguments.
    """

    ap = argparse.ArgumentParser()

    ap.add_argument("-v", "--vineyard", default="crawford-beck", help="vineyard name")
    ap.add_argument("-b", "--block", default=9, type=int, help="block number")
    ap.add_argument("-d", "--date", required=True, help="date to ingest (yyyy-mm-dd)")

    ap.add_argument("-r", "--rows", default=21, help="number of rows in block")

    return ap.parse_args()


def main(args):
    """
    main ingests the images indicated by the passed args object.
    """

    # Get and protect the 'true' data
    label_file = f_org.get_label_file(args.vineyard, args.block, args.date)
    true_data = pd.read_csv(label_file)

    # Create a symlink to the directory to ingest
    linkname = os.path.join(f_org.home, "ingest", "raw_images")
    os.unlink(linkname)
    args.raw_dir = f_org.get_image_path(args.vineyard, args.block, args.date)
    os.symlink(args.raw_dir, linkname)

    # Ingest steps that can be run individually with -s / --step argument
    steps = [
        gen_csv.main,
        pad_csv.main,
        row_pred.main,
        bay_pred.main,
        rename_files.main,
    ]

    # Run all the ingest steps
    df = None
    for s in steps:
        df = s(f_org, args, df=df)

    true_data = true_data.sort_values(["name"])
    df = df.sort_values(["name"])

    true_data.info()
    df.info()

    print("Row Accuracy:", metrics.accuracy_score(true_data["row"], df["row"]))
    print("Bay Accuracy:", metrics.accuracy_score(true_data["bay"], df["pred_bay"]))


if __name__ == "__main__":
    main(parse_args())
