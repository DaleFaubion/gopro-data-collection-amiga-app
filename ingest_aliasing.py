import os

import __init__
from organization import file_org as f_org

import argparse


def create_aliases(image_dir, alias_dir):
    """
    create_aliases creates symlinks to the correct images in the ingest directory
    """
    idx = 0

    for root, dirs, files in [os.walk(im_dir) for im_dir in image_dir]:
        print(files)


def arg_parse():
    """
    Function to get arguments from the command line input.
    """

    ap = argparse.ArgumentParser()
    ap.add_argument("-top", required=True, nargs="+", help="path to top camera images")
    ap.add_argument(
        "-middle", required=True, nargs="+", help="path to middle camera images"
    )
    ap.add_argument(
        "-bottom", required=True, nargs="+", help="path to bottom camera images"
    )

    return vars(ap.parse_args())


if __name__ == "__main__":
    args = arg_parse()
    image_path = os.path.join(f_org.home, "ingest", "raw_images")

    for d in ["top", "middle", "bottom"]:
        os.makedirs(os.path.join(image_path, d))
        create_aliases(args[d], os.path.join(image_path, d))
