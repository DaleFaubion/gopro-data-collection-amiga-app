import os
import shutil

import __init__
from organization import file_org as f_org

import argparse


def create_aliases(image_dir, alias_dir):
    """
    create_aliases creates symlinks to the correct images in the ingest directory
    """

    images = []

    for im_dir in image_dir:
        for root, dirs, files in os.walk(im_dir):
            images.extend([os.path.join(root, f).replace(" ", "\\ ") for f in files])

    for idx in range(len(images)):
        print(os.path.join(alias_dir, str(idx) + ".JPG"), images[idx])
        os.symlink(images[idx], os.path.join(alias_dir, str(idx) + ".JPG"))


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
        alias_dir = os.path.join(image_path, d) + "_camera"
        if not os.path.isdir(alias_dir):
            os.makedirs(alias_dir)

        # Clear out the alias directory before starting
        for file in filter(lambda x: x[-4:] == ".JPG", os.listdir(alias_dir)):
            os.unlink(os.path.join(alias_dir, file))

        create_aliases(args[d], alias_dir)
