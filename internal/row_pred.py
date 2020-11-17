# Fall 2020
# Vinetech Row Prediction
# Ingest Step 3

import pandas as pd
import numpy as np

from .common import *

from sklearn.cluster import KMeans, SpectralClustering

import matplotlib.pyplot as plt


def delta(df, idx, col):
    """
    delta returns a smoothed gradient of the column.
    """

    dcol = np.gradient(df.loc[idx, col])
    dcol -= np.median(dcol)

    dcol = np.clip(dcol, -2 * np.std(dcol), 2 * np.std(dcol))
    return np.convolve(dcol, np.ones((4,)) / 4, mode="same")


def rough_clusers(df, idx, dcol, col):
    """
    rough_clusers returns a column with approximate cluster groupings.
    This will generally return way more clusters than needed which will be corrected
    in subsequent steps
    """

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
    """
    adjust_clusers reorders the predicted clusters to be in chronological order.
    Assumes that the block is recorded from row 1 onward.
    """

    clusters = {}
    order = []
    r = 1

    dest = df.loc[idx, col].copy()

    for i in df.loc[idx, col].unique():
        ix = np.logical_and(idx, df[col] == i)
        clusters[i] = np.median(df.loc[ix, ["ts"]])
        order.append(clusters[i])
        dest[ix] = clusters[i]

    order.sort()

    for i in dest.unique():
        ix = np.logical_and(idx, dest == i)
        dest[ix] = order.index(i) + 1

    return dest


def main(f_org, args, df=None):
    """
    main predicts the row numbers from the ingested gps data.
    """

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
        dx = delta(df, idx, "lat")
        dx -= np.min(dx)
        dx /= np.max(dx)
        df.loc[idx, "dlat"] = (dx - 0.5) / 10

        # This is a hacky approximation of clusters
        df.loc[idx, "row"] = rough_clusers(df, idx, "dlat", "row")

        try:
            # Kmeans clustering!
            km = KMeans(n_clusters=args.rows)
            df.loc[idx, "row"] = km.fit_predict(df.loc[idx, ["ts", "dlat", "row"]])

        except:
            print("GPS Data on camera %s too corrupt to predict rows" % cam)
            continue

        # This reorders the randomly assigned clusters into rows
        #  assumes images are taken in order by row
        df.loc[idx, "row"] = adjust_clusers(df, idx, "row")

    df[columns].to_csv(label_file)
    return df[columns]
