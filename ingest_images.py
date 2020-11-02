import os
import argparse


import __init__
from organization import file_org as f_org
from internal import gen_csv, pad_csv, row_pred, bay_pred


def parse_args():
    ap = argparse.ArgumentParser()

    ap.add_argument("-v", "--vineyard", default="crawford-beck", help="vineyard name")
    ap.add_argument("-b", "--block", default=9, type=int, help="block number")
    ap.add_argument("-d", "--date", required=True, help="date to ingest (yyyy-mm-dd)")

    ap.add_argument("-r", "--rows", default=21, help="number of rows in block")

    return ap.parse_args()


def main():
    args = parse_args()

    gen_csv.main(f_org, args)
    pad_csv.main(f_org, args)
    row_pred.main(f_org, args)
    bay_pred.main(f_org, args)


if __name__ == "__main__":
    main()
