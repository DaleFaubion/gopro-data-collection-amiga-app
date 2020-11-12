#

#

import pandas as pd
import numpy as np

from .common import *

from sklearn.cluster import KMeans, SpectralClustering

import matplotlib.pyplot as plt


def delta(df, idx, col):
    dcol = np.gradient(df.loc[idx, col])
    dcol -= np.median(dcol)

    dcol = np.clip(dcol, -2 * np.std(dcol), 2 * np.std(dcol))
    return np.convolve(dcol, np.ones((4,)) / 4, mode="same")


def rough_clusers(df, idx, dcol, col):

    corrections = {}
    row = 1

    # Direction of first entry
    i = idx.index[0]
    p_dx = df.loc[i, dcol] > 0

    dest = df.loc[idx, col].copy()

    for i in idx.index:
        dx = df.loc[i, dcol] > 0

        # Row change
        if dx != p_dx:
            row += 1

        # Mark the row
        dest = row
        p_dx = dx

    return dest


def adjust_clusers(df, idx, col):

    clusters = {}
    r = 1

    dest = df.loc[idx, col].copy()

    for i, row in df.loc[idx, [col]].iterrows():
        pred = row[col]

        # Add the prediction to the cluster mapping
        if pred not in clusters:
            clusters[pred] = r
            r += 1

        # Map the predicted cluster id to a real row number
        dest[i] = clusters[pred]

    return dest


def main(f_org, args, df=None):

    # Open the current csv
    label_file = f_org.get_label_file(args.vineyard, args.block, args.date)
    if df is None:
        df = pd.read_csv(label_file, index_col=False)

    # Generate an ordinal row
    df["ts"] = df["time"].apply(to_ord)
    df["ts"] /= np.max(df["ts"])

    df = df.sort_values(["camera", "ts"], ignore_index=True)

    print("Predicting Rows")

    for cam in df["camera"].dropna().unique():
        idx = df["camera"] == cam

        # Have the weight the direction of change proportionally to the ts col
        dx = delta(df, idx, "lon")
        dx -= np.min(dx)
        dx /= np.max(dx)
        df.loc[idx, "dlon"] = (dx - 0.5) / 10

        # This is a hacky approximation of clusters
        df.loc[idx, "row"] = rough_clusers(df, idx, "dlon", "row")

        try:
            # Kmeans clustering!
            km = KMeans(n_clusters=args.rows)
            df.loc[idx, "row"] = km.fit_predict(df.loc[idx, ["ts", "dlon", "row"]])

        except:
            print("GPS Data on camera %s too corrupt to predict rows" % cam)
            continue

        # This reorders the randomly assigned clusters into rows
        #  assumes images are taken in order by row
        df.loc[idx, "row"] = adjust_clusers(df, idx, "row")

    df[columns].to_csv(label_file)
    return df[columns]
