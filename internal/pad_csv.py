#

# Script to sort the image entries in a csv before making row predictions

import pandas as pd
import numpy as np

import os

import time

from sklearn import linear_model as lin

from internal.common import *


def pad_cameras(df):
    camera_dirs = {}
    for idx in range(len(df)):
        cam = df.loc[idx, "camera"]
        dir_name = os.path.dirname(df.loc[idx, "raw_dir"])
        if cam and dir_name not in camera_dirs:
            camera_dirs[dir_name] = cam

    return df["raw_dir"].apply(lambda x: camera_dirs[os.path.dirname(x)])


def gps_outliers(df):
    lat = df["lat"] + df["lon"]

    # GPS data for a given block should be within +- 1 degree of the mean,
    #  blocks are very small in terms of coordinates
    return np.abs(lat - np.median(lat)) > 1


def main(f_org, args, df=None):
    # Open the current csv
    label_file = f_org.get_label_file(args.vineyard, args.block, args.date)
    if df is None:
        df = pd.read_csv(label_file, index_col=False)

    print("Padding Camera Metadata")

    # Pads corrupted camera names, assumes that images in a directory will be from
    #  the same camera
    df["camera"] = pad_cameras(df)

    # Pad corrupted time stamps, assumes that images are named chronologically
    df = df.sort_values(["camera", "raw_dir"], ignore_index=True)

    print("Padding Timestamp Metadata")

    # Create time column for k-neighbors
    df["ts"] = df["time"].apply(to_ord)
    df["ts"] = df["ts"].interpolate()
    df["time"] = df["ts"].apply(from_ord)

    print("Padding GPS Metadata")

    # Get the corrupted gps data indices
    corrupt_gps = gps_outliers(df)

    # Correct corrputed latitude / longitude
    for c in df["camera"].dropna().unique():
        # Get the index of valid gps data
        valid = np.logical_and(df["camera"] == c, np.invert(corrupt_gps))
        corrupt = np.logical_and(df["camera"] == c, corrupt_gps)

        if not any(corrupt):
            continue

        # Fit the latitude predictor model
        lat_model = lin.LinearRegression()
        X, y = df.loc[valid, ["ts"]], df.loc[valid, ["lat"]]
        lat_model.fit(X, y)

        # Predict corrupted latitude data
        df.loc[corrupt, ["lat"]] = lat_model.predict(df.loc[corrupt, ["ts"]])

        # Fit the longitude predictor model
        lon_model = lin.LinearRegression()
        X, y = df.loc[valid, ["ts"]], df.loc[valid, ["lon"]]
        lat_model.fit(X, y)

        # Predict corrupted longitude data
        df.loc[corrupt, ["lon"]] = lat_model.predict(df.loc[corrupt, ["ts"]])

    # Sort the dataframe again
    df = df.sort_values(["camera", "time"], ignore_index=True)

    # Shave off computation columns and save
    df = df[columns]
    df.to_csv(label_file, index=False)
    return df
