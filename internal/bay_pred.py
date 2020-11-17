# Fall 2020
# Vinetech Bay Prediction
# Ingest Step 3

from .common import *

import pandas as pd
import itertools as it

from sklearn import ensemble
from sklearn.model_selection import train_test_split

# These ideally would be derived : )
# TODO: pull these values from a csv or somewhere
num_vines = 84
vines_per_bay = 4
first_bay = 4.5

# I hand labeled this date's bays
labeled_date = "2019-06-12"


def pred_bay(x):
    """
    pred_bay does a rough estimate of the bay number based on latitude only and the
    known bay spacing.
    """

    if x < first_bay:
        return 1
    if x > num_vines:
        x = num_vines

    return 2 + int((x - first_bay) / vines_per_bay)


def prep_data(df):
    """
    prep_data returns the training and prediction columns derived from the dataframe.
    """

    # Generate an ordinal row
    df["ts"] = df["time"].apply(to_ord)
    df["ts"] /= np.max(df["ts"])

    # Fill in some values
    df = df.sort_values(["camera", "ts"])
    df["camera"] = df["camera"].interpolate()
    df["row"] = df["row"].interpolate()

    # Calculate relative latitude in [0, 1] range for block
    df["rel_lat"] = df["lat"] - np.min(df["lat"])
    df["rel_lat"] = df["rel_lat"] / np.max(df["rel_lat"])
    df["dir"] = False

    for cam, row in it.product(df["camera"].unique(), df["row"].unique()):
        idx = np.logical_and(df["camera"] == cam, df["row"] == row)

        # Scale the latitude into an approximate vine number
        lats = df.loc[idx, "lat"]
        lats -= np.min(lats)
        lats *= num_vines / np.max(lats)
        df.loc[idx, "p_bay"] = lats.apply(lambda x: pred_bay(x))

        # Calculate relative latitude in [0, 1] range for row
        df.loc[idx, "rel_lat"] -= np.min(df.loc[idx, "rel_lat"])
        df.loc[idx, "rel_lat"] /= np.max(df.loc[idx, "rel_lat"])

        # Scale to the relative time spent walking that row
        ts = df.loc[idx, "ts"]
        ts = -ts if (row % 2) == 0 else ts
        ts -= np.min(ts)
        ts /= np.max(ts)
        df.loc[idx, "rel_ts"] = ts

        # Calculate the direction of travel for the row
        df.loc[idx, "dir"] = np.median(np.gradient(df.loc[idx, "lat"])) > 0

    return df[["p_bay", "lon", "rel_ts", "dir", "rel_lat"]], df["bay"]


def train_model(f_org, model, vineyard="crawford-beck", block=9, **kwargs):
    """
    train_model opens the labeled date of images and trains the given model to predict
    bays.
    """

    # Train a random forest on the hand labeled data
    training_data = f_org.get_label_file(vineyard, block, labeled_date)
    training = pd.read_csv(training_data, index_col=False)
    X, y = prep_data(training)

    print("Training model on hand-labeled date: %s" % labeled_date)

    # Train on 80% of the data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
    model.fit(X_train, y_train)

    # Evaluate the model on the test data
    score = model.score(X_test, y_test)
    print("Trained model with accuracy: %02.3f" % (100 * score))

    return model, score


def main(f_org, args, df=None):
    """
    main trains a bay predictor model on the hand-labeled data and predics the bays of
    the data being ingested.
    """

    # Open the current csv
    label_file = f_org.get_label_file(args.vineyard, args.block, args.date)
    if df is None:
        df = pd.read_csv(label_file, index_col=False)

    print("Predicting Bays")

    # Train a bay predictor on hand-labeled data from 2019
    model, _ = train_model(f_org, ensemble.RandomForestClassifier(), **vars(args))

    # Use the trained forest to predict bays
    try:
        X, _ = prep_data(df)
        df["pred_bay"] = model.predict(X)
        print("Writing bay predictions")
    except:
        print("GPS Data too corrupt to predict bays")
        print("rerun with -s param to walk through ingest steps and view csv file")

    df[columns].to_csv(label_file)
    return df[columns]
