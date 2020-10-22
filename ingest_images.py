# Spring 2020
# VineTech Initial Image Ingest

"""
Ingests images placed in the `raw_images` folder of this project

"""

if __name__ == "__main__":
    import __init__

import pandas as pd
import numpy as np

import argparse
import os

from sklearn.preprocessing import StandardScaler
from preprocessing import Data_Preprocessor as dP
from preprocessing import util as u
from preprocessing.predict_bays import Bay_Predictor

from PIL import Image, ImageTk
from PIL.ExifTags import TAGS, GPSTAGS

from organization import file_org as f_org

columns = [
    "vineyard",
    "block",
    "date",
    "name",
    "time",
    "camera",
    "angle",
    "lat",
    "lon",
    "row",
    "bay",
    "pred_bay",
    "vine_l",
    "vine_r",
    "focal_length",
    "exposure_time",
]


def deg_to_float(value):
    """
    Converts the given latitude or longitude in degrees into a float.
    """

    d = float(value[0][0]) / float(value[0][1])
    m = float(value[1][0]) / float(value[1][1])
    s = float(value[2][0]) / float(value[2][1])
    return d + (m / 60.0) + (s / 3600.0)


def extract(image, prnt=False):
    """
    Extracts the metadata from an image returning a dictionary with hand-picked
    metadata.
    """

    # Setup
    data = {}
    info = image._getexif()

    # Iterate through all metadata
    # TODO: speed up using distinct tags instead of iterating over all
    for tag, value in info.items():
        # Convert tag to readable key
        key = TAGS.get(tag, tag)
        if prnt:
            print(key, value)

        # Handle GPS data
        if key == "GPSInfo":
            data["lat"] = deg_to_float(value[2])
            if value[1] == "S":
                data["lat"] *= -1
            data["lon"] = deg_to_float(value[4])
            if value[3] == "W":
                data["lon"] *= -1

        # Handle Exposure Time
        elif key == "ExposureTime":
            data["exposure_time"] = value[1]

        # Handle Date and Time
        elif key == "DateTimeDigitized":
            date, time = value.split(" ")
            data["date"] = date
            data["time"] = time

        # Handle Focal Length
        # TODO: Find more useful metadata than focal length (always 15)
        elif key == "FocalLengthIn35mmFilm":
            data["focal_length"] = value

        # Handle camera serial number
        elif key == "BodySerialNumber":
            try:
                data["camera"] = int(value[1:14])
            except:
                data["camera"] = np.NaN
    return data


def filter_JPGS(folder):
    """
    Returns a list containing all of the JPGs in the given folder.
    """

    return list(filter(lambda x: ".JPG" in x, os.listdir(folder)))


def fill_gaps(df, path, prnt=True, force_new=False):
    """
    Fills the metadata columns of the dataframe by extracting image metadata.
    """

    # Setup
    data_cols = [
        "lat",
        "lon",
        "exposure_time",
        "time",
        "date",
        "focal_length",
        "camera",
    ]

    # Iterate over dataframe
    for row in df.index:
        # Get file
        filename = df["name"][row]
        if prnt:
            print("Reading:", filename, end="\r")

        # Overwrite data if 'force_new' or if missing
        if force_new or pd.isna(df.loc[row, data_cols]).any():
            # Get metadata
            image = Image.open(os.path.join(path, filename))
            data = extract(image)

            # Fill needed columns
            for col in data_cols:
                if (pd.isnull(df[col][row]) or force_new) and col in data:
                    df.loc[row, col] = data[col]
    return df


def clean_columns(in_df):
    """
    Sorts columns and adds any missing ones since update.
    """

    out_df = in_df.copy()

    for col in columns:
        out_df[col] = in_df[col] if col in in_df.columns else np.NaN

    return out_df


def complete_df(df, img_path, backup_path=None, force_new=False, row_range=None):
    """
    Sorts, and completes a 'locations.csv' dataframe using the most developed
    location prediction methods in the data_preprocessing module.

    TODO: change dtype so that ingest doesn't break where patch is fine.
    """

    print("Getting Image Metadata")
    df = fill_gaps(df, img_path, force_new=force_new)
    df = clean_columns(df)

    # Clean camera column
    df["camera"] = u.smooth_column(df, "camera", dist=10)
    df["camera"] = u.smooth_column(df, "camera", dist=2)
    df["camera"] = u.smooth_column(df, "camera", dist=1)

    # Set the datatype of columns that need to be floats for calculations
    df["lat"] = df["lat"].astype(np.float32)
    df["lon"] = df["lon"].astype(np.float32)

    if backup_path:
        df.to_csv(backup_path)

    print("Sorting Images                         ")
    df.sort_values(by=["angle", "camera", "date", "time"], inplace=True)
    df.reset_index(drop=True, inplace=True)

    # Remove outliers
    dfP = dP.Data_Preprocessor(df)
    dfP.remove_std_outliers(col_name="lat", split_cols=["camera"])
    dfP.remove_std_outliers(col_name="lon", split_cols=["camera"])

    # Location predictions
    print("Predicting Blocks")
    dfP.predict_blocks()

    print("Predicting Rows")
    dfP.predict_rows(row_range=row_range)

    print("Predicting Bays")
    df = dfP.get_df()
    bp = Bay_Predictor()

    if not bp.fit:

        print("Training RandomForestClassifier for bay prediction")

        vineyard = "crawford-beck"
        block = 9
        date = "2019-06-12"

        bp.train_model(
            dates=date, holdout_rows=list(range(15, 22)), vineyard=vineyard, block=block
        )

        score = bp.test_model(
            dates=date, holdout_rows=list(range(15)), vineyard=vineyard, block=block
        )

        print("Model Scored:", score)

    df["pred_bay"] = bp.predict_bays(
        df.loc[0, "vineyard"], df.loc[0, "block"], df.loc[0, "date"].replace(":", "-")
    )

    return df


def save_df(df, file_path, backup=None):
    """
    A Function to save the dataframe to file and display while doing so.
    """

    # Get shorter name for file
    common = os.path.commonprefix([file_path, f_org.root])
    disp_path = os.path.relpath(file_path, common)

    # Get shorter name for backup file
    if not backup is None:
        b_common = os.path.commonprefix([backup, f_org.root])
        b_disp = os.path.relpath(backup, b_common)

    # Save and display
    print("Saving to", disp_path, end="\r")
    df.to_csv(file_path)
    if not backup is None:
        df.to_csv(backup)
    print("Saved to:", disp_path, "    ")


def patch(vineyard, block, date, force_new=False, row_range=None):
    """
    For when the initial call to ingest breaks after some point.  This function
    picks up wherever ingest left off and completes the dataframe.
    """

    # Get paths
    image_path = f_org.ensure_path(f_org.home, "ingest", "processed", date)
    label_path = f_org.ensure_path(f_org.home, "ingest", date)
    label_file = os.path.join(label_path, "locations.csv")
    backup = os.path.join(label_path, "backups", "locations_copy.csv")

    # Get the dataframe
    if os.path.isfile(label_file):
        df = pd.read_csv(label_file, index_col=[0])
    else:
        df = pd.read_csv(backup, index_col=[0])

    print("Patching:", label_file)
    for column in columns:
        if not column in df.columns:
            df[column] = np.NaN

    # Fill the dataframe
    df = complete_df(
        df, image_path, backup_path=backup, force_new=force_new, row_range=row_range
    )

    save_df(df, label_file)

    return df


def ingest_images(vineyard, block, date, row_range=None):
    """
    Ingest function.  Read the documentation in the README.md for usage.
    """

    # Get paths
    image_path = os.path.join(f_org.home, "ingest", "raw_images")
    image_out_path = f_org.ensure_path(f_org.home, "ingest", "processed", date)
    label_path = f_org.ensure_path(f_org.home, "ingest", date)
    label_file = os.path.join(label_path, "locations.csv")
    backup_path = f_org.ensure_path(os.path.join(label_path, "backups"))
    backup_file = os.path.join(backup_path, "locations_copy.csv")

    # Create label file if it doesn't exist
    if os.path.isfile(label_file):
        label_file = os.path.join(label_path, "locations_1.csv")
    if not os.path.isdir(image_out_path):
        os.makedirs(image_out_path)

    # Setup
    id = 0
    df = pd.DataFrame(columns=columns)

    def process_files(angle_num, angle_name):
        """
        Sub-function for processing a certain camera angle.
        """

        nonlocal id

        # Check that there are actually pictures for the angle
        if os.path.isdir(os.path.join(image_path, angle_name)):
            # Process only the images
            for filename in filter_JPGS(os.path.join(image_path, angle_name)):
                # Get the filename, and generate a new one
                print(filename, end="\r")
                name = date + "_" + str(id) + ".JPG"

                # Initial dataframe entry
                df.loc[id, ["name"]] = name
                df.loc[id, ["angle"]] = angle_num

                # Move the file
                old_name = os.path.join(image_path, angle_name, filename)
                new_name = os.path.join(image_out_path, name)
                # copyfile(old_name, new_name)
                os.rename(old_name, new_name)

                id += 1

    print("Processing Images into DataFrame")
    process_files(0, "top_camera")
    process_files(1, "bottom_camera")
    process_files(2, "middle_camera")

    # Add knowns
    df["vineyard"] = vineyard
    df["block"] = int(block)
    df["date"] = date

    # Partial save
    df.to_csv(backup_file)
    print("Saving df")

    # Fill the dataframe metadata
    df = complete_df(
        df, image_out_path, backup_path=backup_file, force_new=True, row_range=row_range
    )

    save_df(df, label_file, backup=backup_file)

    return df


def arg_parse():
    """
    Function to get arguments from the command line input.
    """

    ap = argparse.ArgumentParser()
    ap.add_argument(
        "-v", "--vineyard", required=True, help="vineyard's images to process"
    )
    ap.add_argument("-d", "--date", required=True, help="date of images to process")
    ap.add_argument("-b", "--block", type=int, help="block that images came from")
    ap.add_argument(
        "-rr", "--row_range", type=int, nargs=2, help="range of rows present at ingest"
    )
    ap.add_argument(
        "-i",
        "--ingest",
        action="store_true",
        help="whether to ingest images from folder",
    )
    ap.add_argument(
        "-p",
        "--patch",
        action="store_true",
        help="whether to patch the existing dataframe",
    )
    ap.add_argument("-md", "--metadata", help="image to parse metadata from")
    ap.add_argument(
        "-fn",
        "--force_new",
        action="store_true",
        help="whether to re-ingeest all image metadata",
    )
    return vars(ap.parse_args())


def main(args):
    """
    Main function to ingest images, or display metadata.
    """

    if args["ingest"]:
        ingest_images(
            args["vineyard"], args["block"], args["date"], row_range=args["row_range"]
        )

    if args["patch"]:
        patch(
            args["vineyard"], args["block"], args["date"], force_new=args["force_new"]
        )

    if not args["metadata"] is None:
        path = os.path.join(
            f_org.get_image_path(args["vineyard"], args["block"], args["date"]),
            args["metadata"] + ".JPG",
        )
        print(extract(Image.open(path), prnt=True))


if __name__ == "__main__":
    args = arg_parse()
    main(args)
