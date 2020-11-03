#

# Script to sort the image entries in a csv before making row predictions

import pandas as pd
import numpy as np

import os

import time

from sklearn import linear_model as lin
from sklearn import ensemble as en
from sklearn.model_selection import train_test_split
from sklearn import metrics

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
    return np.logical_or(np.abs(lat - np.median(lat)) > 1, pd.isnull(lat))


def train_model(df, idx, col, model):
    if idx is None:
        X, y = df[["ts"]], df[col]
    else:
        X, y = df.loc[idx, ["ts"]], df.loc[idx, col]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
    model.fit(X_train, y_train)

    # Evaluate the model on the test data
    y_pred = model.predict(X_test)

    # Scale both predictions and true data to [0:1] range
    y_pred, y_test = y_pred - np.min(y_test), y_test - np.min(y_test)
    y_pred, y_test = y_pred / np.max(y_test), y_test / np.max(y_test)

    score = 1 - metrics.mean_squared_error(y_test, y_pred)
    print("Trained %s model with accuracy: %02.3f" % (col, 100 * score))

    return model, score


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

        print(len(df), len(df[df["camera"] == c]), len(df[valid]), len(df[corrupt]))
        print(
            float(np.min(df.loc[corrupt, ["lat"]])),
            float(np.min(df.loc[corrupt, ["lon"]])),
        )

        if len(df[corrupt]) == 0:
            print("Skipping")
            print(df.loc[corrupt, ["lat", "lon"]].head())
            print(df.loc[valid, ["lat", "lon"]].head())
            continue

        # Fit the latitude predictor model
        model, _ = train_model(df, valid, "lat", en.RandomForestRegressor())

        # Predict corrupted latitude data
        df.loc[corrupt, ["lat"]] = model.predict(df.loc[corrupt, ["ts"]])

        # Fit the longitude predictor model
        model, _ = train_model(df, valid, "lon", en.RandomForestRegressor())

        # Predict corrupted longitude data
        df.loc[corrupt, ["lon"]] = model.predict(df.loc[corrupt, ["ts"]])

        print(
            float(np.min(df.loc[corrupt, ["lat"]])),
            float(np.min(df.loc[corrupt, ["lon"]])),
        )

    # Sort the dataframe again
    df = df.sort_values(["camera", "time"], ignore_index=True)

    # Shave off computation columns and save
    df = df[columns]
    df.to_csv(label_file, index=False)
    return df
