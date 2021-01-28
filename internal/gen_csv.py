# Fall 2020
# Vinetech Metadata Ingest
# Ingest Step 0

import os
import pandas as pd

from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS

from .common import *

tag_keys = {}


def get_exif(info, tag):
    """
    get_exif pulls the value from the exif info, caching the correct key for the tag.
    """

    if not tag in tag_keys:
        for (k, v) in info.items():
            tag_keys[TAGS[k] if k in TAGS else GPSTAGS[k]] = k

    key = tag_keys[tag] if tag in tag_keys else None
    return info[key] if key in info else None


def deg_to_float(value):
    """
    deg_to_float converts the given latitude or longitude in degrees into a float.

    This function needs to handle datain the format ((d, x), (m, x), (s, x)) or
    (d, m, s).  This is hacky
    """

    try:
        value = (
            float(value[0][0]) / float(value[0][1]),
            float(value[1][0]) / float(value[1][1]),
            float(value[2][0]) / float(value[2][1]),
        )
    except:
        pass

    return value[0] + (value[1] / 60.0) + (value[2] / 3600.0)


def parse_camera(info):
    """
    parse_camera returns the camera id number from the image metadata.
    """

    cam = get_exif(info, "BodySerialNumber")

    try:
        return int(cam[1:14])
    except:
        return None


def parse_gps(info):
    """
    parse_gps parses gps info from the image metadata.
    """

    info = get_exif(info, "GPSInfo")

    try:
        lat, lon = deg_to_float(info[2]), deg_to_float(info[4])
        if info[1] == "S":
            lat *= -1
        if info[3] == "W":
            lon *= -1

        return lat, lon
    except:
        return np.nan, np.nan


def parse_time(info):
    """
    parse_time parses the timestamp from gps metadata.
    """

    time = get_exif(info, "DateTimeDigitized")

    try:
        return time.split(" ")[1]
    except:
        return None


def main(f_org, args, df=None):
    """
    main creates a pandas dataframe and fills it with the metadata that can be parsed
    from the images.
    """

    # Get the label file
    label_file = f_org.get_label_file(args.vineyard, args.block, args.date)
    if not os.path.isdir(os.path.dirname(label_file)):
        os.makedirs(os.path.dirname(label_file))

    # Create the initial dataframe
    df = pd.DataFrame(columns=columns)
    idx = 0

    print("Reading Image Metadata")

    # Walk the directory of images
    for root, dirs, files in os.walk(args.raw_dir, followlinks=True):
        for f in files:
            print("\r", f, end=" ")

            # Open the image
            with Image.open(os.path.join(root, f)) as img:
                info = img.getexif()

                # Extract the metadata
                df.loc[idx, "raw_dir"] = os.path.join(root, f)
                df.loc[idx, "time"] = parse_time(info)
                df.loc[idx, "camera"] = parse_camera(info)
                df.loc[idx, ["lat", "lon"]] = parse_gps(info)
                df.loc[idx, "focal_length"] = get_exif(info, "FocalLengthIn35mmFilm")
                df.loc[idx, "exposure_time"] = get_exif(info, "ExposureTime")

            idx += 1

    print("\rGenerating CSV                ")
    df["vineyard"] = args.vineyard
    df["block"] = args.block
    df["date"] = args.date.replace("-", ":")
    df.to_csv(label_file, index=False)

    return df
