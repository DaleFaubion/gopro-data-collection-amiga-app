import os
import argparse


import __init__
from organization import file_org as f_org
from internal import gen_csv, pad_csv, row_pred, bay_pred, rename_files


def parse_args():
    ap = argparse.ArgumentParser()

    ap.add_argument("-v", "--vineyard", default="crawford-beck", help="vineyard name")
    ap.add_argument("-b", "--block", default=9, type=int, help="block number")
    ap.add_argument("-d", "--date", required=True, help="date to ingest (yyyy-mm-dd)")

    ap.add_argument("-r", "--rows", default=21, help="number of rows in block")
    ap.add_argument("-raw_dir", help="directory of unprocessed images")

    ap.add_argument("-s", "--step", type=int, help="step to run")

    return ap.parse_args()


def main():
    args = parse_args()

    if args.raw_dir:
        linkname = os.path.join(f_org.home, "ingest", "raw_images")
        os.unlink(linkname)
        args.raw_dir = args.raw_dir.replace("~", f_org.home)
        os.symlink(args.raw_dir, linkname)

    steps = [
        gen_csv.main,
        pad_csv.main,
        row_pred.main,
        bay_pred.main,
        rename_files.main,
    ]

    if args.step is not None:
        steps[args.step](f_org, args)
        return

    df = None
    for s in steps:
        df = s(f_org, args, df=df)


if __name__ == "__main__":
    main()
