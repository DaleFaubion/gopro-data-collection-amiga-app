#

#

from internal.common import *

import pandas as pd
import itertools as it

from sklearn import ensemble
from sklearn.model_selection import train_test_split

# These ideally would be derived : )
num_vines = 84
vines_per_bay = 4
first_bay = 4.5

# I hand labeled this date's bays
labeled_date = "2019-06-12"


def pred_bay(x):
    if x < first_bay:
        return 1
    if x > num_vines:
        x = num_vines

    return 2 + int((x - first_bay) / vines_per_bay)


def prep_data(df):
    # Generate an ordinal row
    df["ts"] = df["time"].apply(to_ord)
    df["ts"] /= np.max(df["ts"])

    df = df.sort_values(["camera", "ts"])
    df["camera"] = df["camera"].interpolate()
    df["row"] = df["row"].interpolate()

    for cam, row in it.product(df["camera"].unique(), df["row"].unique()):
        idx = np.logical_and(df["camera"] == cam, df["row"] == row)

        # Scale the latitude into an approximate vine number
        lats = df.loc[idx, "lon"]
        lats -= np.min(lats)
        lats *= num_vines / np.max(lats)
        df.loc[idx, "p_bay"] = lats.apply(lambda x: pred_bay(x))

        # Scale to the relative time spent walking that row
        ts = df.loc[idx, "ts"]
        ts = -ts if (row % 2) == 0 else ts
        ts -= np.min(ts)
        ts /= np.max(ts)
        df.loc[idx, "rel_ts"] = ts

        df.loc[idx, "dir"] = row % 2

    return df[["p_bay", "lon", "rel_ts", "dir"]], df["bay"]


def train_model(f_org, model, vineyard="crawford-beck", block=9):

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

    # Open the current csv
    label_file = f_org.get_label_file(args.vineyard, args.block, args.date)
    if df is None:
        df = pd.read_csv(label_file, index_col=False)

    print("Predicting Bays")

    model, _ = train_model(
        f_org,
        ensemble.RandomForestClassifier(),
        vineyard=args.vineyard,
        block=args.block,
    )

    # Use the trained forest to predict bays
    X, _ = prep_data(df)
    df["bay"] = model.predict(X)

    print("Writing bay predictions")

    df[columns].to_csv(label_file)
    return df[columns]
