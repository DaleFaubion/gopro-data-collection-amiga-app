# Fall 2020
# Vinetech Image Ingest Script

import os
import argparse


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
    ap.add_argument("-raw_dir", help="directory of unprocessed images")

    ap.add_argument("-s", "--step", type=int, help="step to run")

    return ap.parse_args()


def main(args):
    """
    main ingests the images indicated by the passed args object.
    """

    if not os.path.isdir(os.path.join(f_org.home, "ingest")):
        os.makedirs(os.path.join(f_org.home, "ingest"))

    # Create a symlink to the directory to ingest
    if args.raw_dir:
        linkname = os.path.join(f_org.home, "ingest", "raw_images")
        if os.path.isdir(linkname) or os.path.islink(linkname):
            os.unlink(linkname)
        args.raw_dir = args.raw_dir.replace("~", f_org.home)
        os.symlink(args.raw_dir, linkname)

        if not len(os.listdir(args.raw_dir)):
            print("Chosen path does not contain files")
            print("Make sure to run setup.sh from the root repo")
            return

    elif os.listdir(f_org.get_image_path(args.vineyard, args.block, args.date)):
        args.raw_dir = f_org.get_image_path(args.vineyard, args.block, args.date)
    else:
        print("Default path is empty, select the correct path with -raw_dir argument")
        return

    # Ingest steps that can be run individually with -s / --step argument
    steps = [
        gen_csv.main,
        pad_csv.main,
        row_pred.main,
        bay_pred.main,
        rename_files.main,
    ]

    # Run a single ingest step for debugging
    if args.step is not None:
        steps[args.step](f_org, args)
        return

    # Run all the ingest steps
    df = None
    for s in steps:
        df = s(f_org, args, df=df)


if __name__ == "__main__":
    main(parse_args())
